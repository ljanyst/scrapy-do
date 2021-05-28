#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   26.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import os
import json
import time
import psutil
import socket
import urllib
import os.path
import mimetypes

from autobahn.twisted.resource import WebSocketResource
from dateutil.relativedelta import relativedelta
from twisted.internet.defer import inlineCallbacks
from twisted.cred.checkers import FilePasswordDB
from twisted.web.resource import IResource
from twisted.cred.portal import IRealm, Portal
from twisted.web.server import NOT_DONE_YET
from twisted.web.guard import HTTPAuthSessionWrapper, DigestCredentialFactory
from scrapy_do.utils import get_object
from zope.interface import implementer
from twisted.web import resource
from .websocket import WSFactory, WSProtocol
from .schedule import Status as JobStatus
from scrapy_do import __version__
from datetime import datetime
from pkgutil import get_data
from .utils import arg_require_all, arg_require_any, pprint_relativedelta
from .utils import twisted_sleep


#-------------------------------------------------------------------------------
class WebApp(resource.Resource):
    #---------------------------------------------------------------------------
    def __init__(self, config, controller):
        super(WebApp, self).__init__()
        self.config = config
        self.controller = controller
        self.children = {}

        #-----------------------------------------------------------------------
        # Register web modules
        #-----------------------------------------------------------------------
        web_modules = config.get_options('web-modules')

        for mod_name, mod_class_name in web_modules:
            mod_class = get_object(mod_class_name)
            self.putChild(mod_name.encode('utf-8'), mod_class(self))

        #-----------------------------------------------------------------------
        # Set up the websocket
        #-----------------------------------------------------------------------
        ws_factory = WSFactory(controller=self.controller)
        ws_factory.protocol = WSProtocol
        ws_resource = WebSocketResource(ws_factory)
        self.putChild(b'ws', ws_resource)

        #-----------------------------------------------------------------------
        # Register UI modules
        #-----------------------------------------------------------------------
        assets = None
        try:
            assets = get_data(__package__, 'ui/asset-manifest.json')
            assets = assets.decode('utf-8')
        except FileNotFoundError:
            self.index = self

        if assets is not None:
            self.index = UIResource('ui/index.html')
            self.putChild(b'', self.index)

            children = [
                '/favicon.png',
                '/manifest.json',
                '/scrapy-do-logo.png'
            ]
            for child in children:
                self.register_child(child, UIResource('ui' + child))

            assets = json.loads(assets)
            for _, asset in assets['files'].items():
                if asset.startswith('/'):
                    asset = asset[1:]
                self.register_child('/' + asset, UIResource('ui/' + asset))

    #---------------------------------------------------------------------------
    def register_child(self, key, resource):
        key = key.encode('utf-8')
        self.children[key] = resource

    #---------------------------------------------------------------------------
    def getChild(self, name, request):
        if request.uri in self.children:
            return self.children[request.uri]
        return self.index

    #---------------------------------------------------------------------------
    def render_GET(self, request):
        data = b'The UI files have not been built.'
        request.setHeader('Content-Type', 'text/plain')
        request.setHeader('Content-Length', str(len(data)))
        return data


#-------------------------------------------------------------------------------
class UIResource(resource.Resource):

    isLeaf = True

    #---------------------------------------------------------------------------
    def __init__(self, name):
        super(UIResource, self).__init__()
        self.name = name
        self.data = get_data(__package__, name)
        mimetype = mimetypes.guess_type(self.name)[0]
        self.mimetype = mimetype if mimetype else 'text/plain'

    #---------------------------------------------------------------------------
    def render_GET(self, request):
        request.setHeader('Content-Type', self.mimetype)
        request.setHeader('Content-Length', str(len(self.data)))
        return self.data


#-------------------------------------------------------------------------------
class JsonResource(resource.Resource):

    isLeaf = True

    #---------------------------------------------------------------------------
    def __init__(self, parent):
        super(JsonResource, self).__init__()
        self.parent = parent

    #---------------------------------------------------------------------------
    def render_json(self, request, data):
        json_data = json.dumps(data, ensure_ascii=False) + '\n'
        json_data = json_data.encode('utf-8')
        request.setHeader('Content-Type', 'application/json')
        request.setHeader('Content-Length', str(len(json_data)))
        request.setHeader('Access-Control-Allow-Origin', '*')
        return json_data

    #---------------------------------------------------------------------------
    def render(self, request):
        try:
            data = super(JsonResource, self).render(request)
            if data == NOT_DONE_YET:
                return data
            data = {
                **{'status': 'ok'},
                **data
            }
            return self.render_json(request, data)
        except Exception as e:
            request.setResponseCode(400)
            data = {
                'status': 'error',
                'msg': str(e)
            }
            return self.render_json(request, data)


#-------------------------------------------------------------------------------
class Status(JsonResource):

    #---------------------------------------------------------------------------
    def render_GET(self, request):
        p = psutil.Process(os.getpid())
        controller = self.parent.controller
        uptime = relativedelta(datetime.now(), controller.start_time)
        all_spiders = \
            [spider
             for _, prj in controller.projects.items()
             for spider in prj.spiders]
        resp = {
            'memory-usage': float(p.memory_info().rss) / 1024. / 1024.,
            'cpu-usage': p.cpu_percent(),
            'time': str(datetime.now()),
            'timezone': "{}; {}".format(time.tzname[0], time.tzname[1]),
            'hostname': socket.gethostname(),
            'uptime': pprint_relativedelta(uptime),
            'jobs-run': controller.counter_run,
            'jobs-successful': controller.counter_success,
            'jobs-failed': controller.counter_failure,
            'jobs-canceled': controller.counter_cancel,
            'jobs-scheduled': len(controller.scheduled_jobs),
            'projects': len(controller.projects),
            'spiders': len(all_spiders),
            'daemon-version': __version__,
        }
        return resp


#-------------------------------------------------------------------------------
class PushProject(JsonResource):

    #---------------------------------------------------------------------------
    def render_POST(self, request):
        @inlineCallbacks
        def do_async():
            try:
                data = request.args[b'archive'][0]
            except KeyError as e:
                result = {
                    'status': 'error',
                    'msg': 'Missing argument: ' + str(e)
                }
                request.setResponseCode(400)
                request.write(self.render_json(request, result))
                request.finish()
                return

            try:
                controller = self.parent.controller

                project = yield controller.push_project(data)
                result = {
                    'status': 'ok',
                    'name': project.name,
                    'spiders': project.spiders
                }
            except Exception as e:
                request.setResponseCode(400)
                result = {'status': 'error', 'msg': str(e)}

            request.write(self.render_json(request, result))
            request.finish()
        do_async()
        return NOT_DONE_YET


#-------------------------------------------------------------------------------
class ListProjects(JsonResource):

    #---------------------------------------------------------------------------
    def render_GET(self, request):
        projects = self.parent.controller.get_projects()
        return {'projects': projects}


#-------------------------------------------------------------------------------
class ListSpiders(JsonResource):

    #---------------------------------------------------------------------------
    def render_GET(self, request):
        arg_require_all(request.args, [b'project'])
        project = request.args[b'project'][0].decode('utf-8')

        spiders = self.parent.controller.get_spiders(project)
        return {'project': project, 'spiders': spiders}


#-------------------------------------------------------------------------------
class ScheduleJob(JsonResource):

    #---------------------------------------------------------------------------
    def render_POST(self, request):
        arg_require_all(request.args, [b'project', b'spider', b'when'])
        project = request.args[b'project'][0].decode('utf-8')
        spider = request.args[b'spider'][0].decode('utf-8')
        when = request.args[b'when'][0].decode('utf-8')

        description = ''
        if b'description' in request.args:
            description = request.args[b'description'][0].decode('utf-8')

        payload = '{}'
        if b'payload' in request.args:
            payload = request.args[b'payload'][0].decode('utf-8')

        job_id = self.parent.controller.schedule_job(project, spider, when,
                                                     description=description,
                                                     payload=payload)
        return {'identifier': job_id}


#-------------------------------------------------------------------------------
class ListJobs(JsonResource):

    #---------------------------------------------------------------------------
    def render_GET(self, request):
        arg_require_any(request.args, [b'status', b'id'])
        if b'status' in request.args:
            status = request.args[b'status'][0].decode('utf-8')
            if status == 'ACTIVE':
                jobs = self.parent.controller.get_active_jobs()
            elif status == 'COMPLETED':
                jobs = self.parent.controller.get_completed_jobs()
            else:
                status = JobStatus[status]
                jobs = self.parent.controller.get_jobs(status)
        else:
            identifier = request.args[b'id'][0].decode('utf-8')
            jobs = [self.parent.controller.get_job(identifier)]

        return {'jobs': [job.to_dict() for job in jobs]}


#-------------------------------------------------------------------------------
class CancelJob(JsonResource):

    #---------------------------------------------------------------------------
    def render_POST(self, request):
        @inlineCallbacks
        def do_async():
            try:
                job_id = request.args[b'id'][0].decode('utf-8')
            except KeyError as e:
                result = {
                    'status': 'error',
                    'msg': 'Missing argument: ' + str(e)
                }
                request.setResponseCode(400)
                request.write(self.render_json(request, result))
                request.finish()
                return

            try:
                controller = self.parent.controller

                yield controller.cancel_job(job_id)
                result = {'status': 'ok'}
            except Exception as e:
                request.setResponseCode(400)
                result = {'status': 'error', 'msg': str(e)}

            request.write(self.render_json(request, result))
            request.finish()
        do_async()
        return NOT_DONE_YET


#-------------------------------------------------------------------------------
class GetLogFile(resource.Resource):

    isLeaf = True

    #---------------------------------------------------------------------------
    def __init__(self, parent):
        super(GetLogFile, self).__init__()
        self.parent = parent

    #---------------------------------------------------------------------------
    def render_GET(self, request):
        @inlineCallbacks
        def do_async():
            request.setHeader('Content-Type', 'text/plain')
            request.setHeader('Access-Control-Allow-Origin', '*')
            controller = self.parent.parent.controller
            
            req_path = request.path
            if isinstance(req_path, bytes):
                req_path = req_path.decode('utf-8')

            filename = os.path.basename(urllib.parse.unquote(req_path))
            filepath = os.path.join(controller.log_dir, filename)
            job_id = os.path.splitext(filename)[0]

            try:
                f = open(filepath, "rb")
            except Exception:
                request.setResponseCode(404)
                request.write('File not found'.encode('utf-8'))
                request.finish()
                return

            while True:
                try:
                    data = f.read()
                    if len(data) == 0:
                        if job_id in controller.running_jobs:
                            yield twisted_sleep(0.25)
                            continue
                        else:
                            break
                    request.write(data)
                except Exception:
                    request.setResponseCode(500)
                    break
            f.close()
            request.finish()

        do_async()
        return NOT_DONE_YET


#-------------------------------------------------------------------------------
class GetLog(resource.Resource):

    isLeaf = False

    #---------------------------------------------------------------------------
    def __init__(self, parent):
        super(GetLog, self).__init__()
        self.parent = parent

    #---------------------------------------------------------------------------
    def getChild(self, name, request):
        return GetLogFile(self)


#-------------------------------------------------------------------------------
class RemoveProject(JsonResource):

    #---------------------------------------------------------------------------
    def render_POST(self, request):
        arg_require_all(request.args, [b'name'])
        name = request.args[b'name'][0].decode('utf-8')
        self.parent.controller.remove_project(name)
        return {}


#-------------------------------------------------------------------------------
@implementer(IRealm)
class PublicHTMLRealm:

    #---------------------------------------------------------------------------
    def __init__(self, config, controller):
        super(PublicHTMLRealm, self).__init__()
        self.config = config
        self.controller = controller

    #---------------------------------------------------------------------------
    def requestAvatar(self, avatar_id, mind, *interfaces):
        if IResource in interfaces:
            return (IResource, WebApp(self.config, self.controller),
                    lambda: None)
        raise NotImplementedError()


#-------------------------------------------------------------------------------
def get_web_app(config, controller):
    auth = config.get_bool('web', 'auth', False)
    if auth:
        auth_file = config.get_string('web', 'auth-db')
        portal = Portal(PublicHTMLRealm(config, controller),
                        [FilePasswordDB(auth_file)])
        credential_factory = DigestCredentialFactory('md5', b'scrapy-do')
        resource = HTTPAuthSessionWrapper(portal, [credential_factory])
        return resource

    return WebApp(config, controller)
