#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   26.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import os
import json
import psutil

from twisted.cred.checkers import FilePasswordDB
from twisted.web.resource import IResource
from twisted.cred.portal import IRealm, Portal
from twisted.web.guard import HTTPAuthSessionWrapper, DigestCredentialFactory
from scrapy_do.utils import get_object
from zope.interface import implementer
from twisted.web import resource


#-------------------------------------------------------------------------------
class WebApp(resource.Resource):

    #---------------------------------------------------------------------------
    def __init__(self, config, controller):
        super(WebApp, self).__init__()
        self.config = config
        self.controller = controller
        self.putChild(b'', Home())

        web_modules = config.get_options('web-modules')

        for mod_name, mod_class_name in web_modules:
            mod_class = get_object(mod_class_name)
            self.putChild(mod_name.encode('utf-8'), mod_class(self))


#-------------------------------------------------------------------------------
class Home(resource.Resource):

    isLeaf = True

    #---------------------------------------------------------------------------
    def render_GET(self, request):
        return "<html>Hello, world!</html>".encode('utf-8')


#-------------------------------------------------------------------------------
class JsonResource(resource.Resource):

    isLeaf = True

    #---------------------------------------------------------------------------
    def __init__(self, parent):
        super(JsonResource, self).__init__()
        self.parent = parent

    #---------------------------------------------------------------------------
    def render(self, request):
        data = super(JsonResource, self).render(request)
        encoder = json.JSONEncoder()
        encoded = encoder.encode(data) + '\n'
        request.setHeader('Content-Type', 'application/json')
        request.setHeader('Content-Length', len(encoded))
        return encoded.encode('utf-8')


#-------------------------------------------------------------------------------
class Status(JsonResource):

    #---------------------------------------------------------------------------
    def render_GET(self, request):
        p = psutil.Process(os.getpid())
        resp = {
            'memory-usage': p.memory_info().rss,
            'cpu-usage': p.cpu_percent()
        }
        return resp


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
