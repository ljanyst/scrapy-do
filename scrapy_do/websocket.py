#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   08.02.2018
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import functools
import calendar
import socket
import psutil
import base64
import time
import json
import os

from autobahn.twisted.websocket import WebSocketServerProtocol
from autobahn.twisted.websocket import WebSocketServerFactory
from dateutil.relativedelta import relativedelta
from twisted.internet.defer import inlineCallbacks
from scrapy_do.controller import Event as ControllerEvent
from twisted.logger import Logger
from scrapy_do import __version__
from datetime import datetime
from tzlocal import get_localzone
from .utils import pprint_relativedelta


#-------------------------------------------------------------------------------
class WSFactory(WebSocketServerFactory):
    """
    Server factory producing configured WSProtocol objects.
    """

    #---------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        self.controller = kwargs.pop('controller')
        super(WSFactory, self).__init__(*args, **kwargs)

    #---------------------------------------------------------------------------
    def buildProtocol(self, addr):
        protocol = super(WSFactory, self).buildProtocol(addr)
        protocol.controller = self.controller
        return protocol


#-------------------------------------------------------------------------------
class WSProtocol(WebSocketServerProtocol):
    """
    Web Socket protocol handling the interaction with the Scrapy Do web front
    end.
    """

    wslog = Logger()

    #---------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super(WSProtocol, self).__init__(*args, **kwargs)
        self.actionHandlers = {}
        self.actionHandlers['PROJECT_REMOVE'] = self.project_remove
        self.actionHandlers['PROJECT_PUSH'] = self.project_push
        self.actionHandlers['JOB_CANCEL'] = self.job_cancel
        self.actionHandlers['JOB_SCHEDULE'] = self.job_schedule

    #---------------------------------------------------------------------------
    def onOpen(self):
        """
        A connection has ben opened, so send the initial daemon state to the
        client.
        """

        self.send_daemon_status()
        self.send_projects_status()
        self.send_jobs_status()
        self.send_project_list()
        self.send_job_list('ACTIVE')
        self.send_job_list('COMPLETED')
        self.controller.add_event_listener(self.on_controller_event)

    #---------------------------------------------------------------------------
    def onMessage(self, payload, isBinary):
        """
        Handle client action such as pushing a new project or scheduling a job.
        """

        #-----------------------------------------------------------------------
        # Check the message validity
        #-----------------------------------------------------------------------
        if isBinary:
            return

        try:
            payload = payload.decode('utf-8')
            data = json.loads(payload)
        except Exception as e:
            self.wslog.debug('Unable to parse message: {}.'.format(str(e)))
            return

        for header in ['type', 'action', 'id']:
            if header not in data:
                msg = 'Header "{}" is missing.'.format(header)
                self.wslog.debug(msg)
                if 'id' in data:
                    self.send_error_response(data['id'], msg)
                return

        if data['type'] != 'ACTION':
            msg = 'Rejecting non-action message: {}.'.format(data['type'])
            self.wslog.debug(msg)
            self.send_error_response(data['id'], msg)
            return

        if data['action'] not in self.actionHandlers:
            msg = 'Unknown action: {}.'.format(data['action'])
            self.wslog.debug(msg)
            self.send_error_response(data['id'], msg)
            return

        #-----------------------------------------------------------------------
        # Execute the action
        #-----------------------------------------------------------------------
        self.actionHandlers[data['action']](data)

    #---------------------------------------------------------------------------
    def onClose(self, wasClean, code, reason):
        """
        The connection has been closed, clean up the state.
        """

        self.controller.remove_event_listener(self.on_controller_event)

    #---------------------------------------------------------------------------
    def send_json(self, msg):
        """
        Convert a message dictionary to JSON and send it over to a client.
        """

        data = json.dumps(msg) + '\n'
        data = data.encode('utf-8')
        self.sendMessage(data)

    #---------------------------------------------------------------------------
    def send_response(self, msg_id, data={}):
        """
        Send response to a client's action.

        :param msg_id: the id of the client's message we're responding to
        :param data:   the body of the response message
        """

        data['id'] = msg_id
        data['type'] = 'ACTION_EXECUTED'
        if 'status' not in data:
            data['status'] = 'OK'
        self.send_json(data)

    #---------------------------------------------------------------------------
    def send_error_response(self, msg_id, error_msg):
        """
        Send an error response a client's action.

        :param msg_id: the id of the client's message we're responding to
        :param error_msg: the error message
        """

        data = {
            'status': 'ERROR',
            'message': error_msg
        }
        self.send_response(msg_id, data)

    #---------------------------------------------------------------------------
    def send_daemon_status(self):
        """
        Send the daemon status to the client.
        """

        p = psutil.Process(os.getpid())
        uptime = relativedelta(datetime.now(), self.controller.start_time)
        uptime = pprint_relativedelta(uptime)
        uptime = ' '.join(uptime.split()[:-1])
        if not uptime:
            uptime = '0m'
        msg = {
            'type': 'DAEMON_STATUS',
            'memoryUsage': int(float(p.memory_info().rss) / 1024. / 1024.),
            'cpuUsage': p.cpu_percent(),
            'time': int(calendar.timegm(time.gmtime())),
            'timezone': str(get_localzone()),
            'hostname': socket.gethostname(),
            'uptime': uptime,
            'daemonVersion': __version__,
        }
        self.send_json(msg)

    #---------------------------------------------------------------------------
    def send_projects_status(self):
        """
        Send the summary of projects to the client.
        """

        controller = self.controller
        all_spiders = [
            spider
            for prj in controller.projects.values()
            for spider in prj.spiders
        ]

        msg = {
            'type': 'PROJECTS_STATUS',
            'projects': len(controller.projects),
            'spiders': len(all_spiders),
        }
        self.send_json(msg)

    #---------------------------------------------------------------------------
    def send_jobs_status(self):
        """
        Send the summary of jobs to the client.
        """

        msg = {
            'type': 'JOBS_STATUS',
            'jobsRun': self.controller.counter_run,
            'jobsSuccessful': self.controller.counter_success,
            'jobsFailed': self.controller.counter_failure,
            'jobsCanceled': self.controller.counter_cancel,
            'jobsScheduled': len(self.controller.scheduled_jobs),
        }
        self.send_json(msg)

    #---------------------------------------------------------------------------
    def send_project_list(self):
        """
        Send the full list of projects to the client.
        """

        projects = self.controller.get_projects()
        projects = functools.reduce(lambda acc, x: acc + [{
            'name': x,
            'spiders': self.controller.get_spiders(x)
        }], projects, [])

        msg = {
            'type': 'PROJECT_LIST',
            'projects': projects
        }
        self.send_json(msg)

    #---------------------------------------------------------------------------
    def send_project_push(self, prj):
        """
        Notify the client about a project being pushed.
        """

        msg = {
            'type': 'PROJECT_PUSH',
            'name': prj.name,
            'spiders': prj.spiders
        }
        self.send_json(msg)

    #---------------------------------------------------------------------------
    def send_project_remove(self, name):
        """
        Notify the client about a project being removed.
        """

        msg = {
            'type': 'PROJECT_REMOVE',
            'name': name
        }
        self.send_json(msg)

    #---------------------------------------------------------------------------
    def process_job(self, job):
        """
        Process a dictionary describing a job and convert it to a form more
        convenient for the client.
        """

        job_dict = job.to_dict()
        logs = self.controller.get_job_logs(job.identifier)
        job_dict['timestamp'] = time.mktime(job.timestamp.timetuple())
        job_dict['outLog'] = False
        job_dict['errLog'] = False
        if logs[0] is not None:
            job_dict['outLog'] = True
        if logs[1] is not None:
            job_dict['errLog'] = True
        return job_dict

    #---------------------------------------------------------------------------
    def send_job_list(self, status):
        """
        Send a full ist of jobs to the client.
        """

        jobs = []
        if status == 'ACTIVE':
            jobs = self.controller.get_active_jobs()
        elif status == 'COMPLETED':
            jobs = self.controller.get_completed_jobs()

        msg = {
            'type': 'JOB_LIST',
            'status': status,
            'jobs': [self.process_job(job) for job in jobs]
        }
        self.send_json(msg)

    #---------------------------------------------------------------------------
    def send_job_update(self, job):
        """
        Notify the client about the job properties being updated.
        """

        msg = {
            'type': 'JOB_UPDATE',
            'job': self.process_job(job)
        }
        self.send_json(msg)

    #---------------------------------------------------------------------------
    def send_job_remove(self, jobId):
        """
        Notify the client about a job being removed.
        """

        msg = {
            'type': 'JOB_REMOVE',
            'jobId': jobId,
        }
        self.send_json(msg)

    #---------------------------------------------------------------------------
    def on_controller_event(self, event_type, event_data):
        """
        Handle controller events and dispatch appropriate messages to the
        client.
        """

        if event_type == ControllerEvent.DAEMON_STATUS_CHANGE:
            self.send_daemon_status()
        elif event_type == ControllerEvent.PROJECT_PUSH:
            self.send_project_push(event_data)
            self.send_projects_status()
        elif event_type == ControllerEvent.PROJECT_REMOVE:
            self.send_project_remove(event_data)
            self.send_projects_status()
        elif event_type == ControllerEvent.JOB_UPDATE:
            self.send_job_update(event_data)
            self.send_jobs_status()
        elif event_type == ControllerEvent.JOB_REMOVE:
            self.send_job_remove(event_data)
            self.send_jobs_status()

    #---------------------------------------------------------------------------
    def project_remove(self, data):
        """
        Execute a project removal request.
        """

        if 'name' not in data:
            self.send_error_response(data['id'], 'Project name not specified.')
            return

        try:
            self.controller.remove_project(data['name'])
            self.send_response(data['id'])
        except Exception as e:
            self.send_error_response(data['id'], str(e))

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def project_push(self, data):
        """
        Execute a project push request.
        """

        if 'archiveData' not in data:
            self.send_error_response(data['id'], 'Project name not specified.')
            return

        try:
            archiveData = base64.b64decode(data['archiveData'])
            project = yield self.controller.push_project(archiveData)
            msg = {
                'name': project.name
            }
            self.send_response(data['id'], msg)
        except Exception as e:
            self.send_error_response(data['id'], str(e))

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def job_cancel(self, data):
        """
        Execute a job cancellation request.
        """

        if 'jobId' not in data:
            self.send_error_response(data['id'], 'Job ID not specified.')
            return

        try:
            yield self.controller.cancel_job(data['jobId'])
            self.send_response(data['id'])
        except Exception as e:
            self.send_error_response(data['id'], str(e))

    #---------------------------------------------------------------------------
    def job_schedule(self, data):
        """
        Execute a job scheduling request.
        """

        for field in ['project', 'spider', 'schedule']:
            if field not in data:
                msg = '{} not specified.'.format(field.title())
                self.send_error_response(data['id'], msg)
                return

        try:
            jobId = self.controller.schedule_job(data['project'],
                                                 data['spider'],
                                                 data['schedule'])
            msg = {
                'jobId': jobId
            }
            self.send_response(data['id'], msg)
        except Exception as e:
            self.send_error_response(data['id'], str(e))
