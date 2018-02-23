#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   08.02.2018
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import base64

from twisted.internet.defer import Deferred, inlineCallbacks
from scrapy_do.controller import Event as ControllerEvent
from scrapy_do.controller import Project
from scrapy_do.schedule import Job, Status, Actor
from scrapy_do.websocket import WSFactory, WSProtocol
from unittest.mock import Mock, patch
from twisted.trial import unittest
from datetime import datetime
from .utils import json_encode, make_deferred_func


#-------------------------------------------------------------------------------
class WebSocketTests(unittest.TestCase):

    #---------------------------------------------------------------------------
    def setUp(self):
        self.controller = Mock()
        controller = self.controller
        controller.counter_run = 0
        controller.start_time.timestamp.return_value = 0
        controller.projects = {}
        controller.scheduled_jobs = []
        controller.counter_cancel = 0
        controller.counter_failure = 0
        controller.counter_success = 0
        controller.counter_run = 0
        controller.start_time = datetime.now()
        controller.get_projects.return_value = ['foo', 'bar']
        controller.get_spiders.return_value = ['foo', 'bar']
        active_jobs = [Job(status=Status.PENDING, actor=Actor.USER)]
        controller.get_active_jobs.return_value = active_jobs
        completed_jobs = [Job(status=Status.CANCELED, actor=Actor.USER)]
        controller.get_completed_jobs.return_value = completed_jobs
        controller.get_job_logs.return_value = (None, None)
        factory = WSFactory(controller=controller)
        factory.protocol = WSProtocol
        self.protocol = factory.buildProtocol(None)

    #---------------------------------------------------------------------------
    def test_server_status(self):
        protocol = self.protocol
        with patch.object(WSProtocol, "sendMessage"):
            protocol.onOpen()
            protocol.onMessage(None, None)
            protocol.onClose(None, None, None)
            protocol.on_controller_event(ControllerEvent.DAEMON_STATUS_CHANGE,
                                         None)

    #---------------------------------------------------------------------------
    def test_action_messages(self):
        protocol = self.protocol
        with patch.object(WSProtocol, "sendMessage"):
            protocol.onMessage(None, True)
            protocol.onMessage(b'foo', False)
            protocol.onMessage(b'{}', False)
            protocol.onMessage(b'{"id": "foo"}', False)
            protocol.onMessage(b'{"id": "foo", "type": "bar", "action": "baz"}',
                               False)
            protocol.onMessage(b'{"id": "a", "type": "ACTION", "action": "b"}',
                               False)

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def test_project_handling(self):
        protocol = self.protocol
        controller = self.controller
        with patch.object(WSProtocol, "sendMessage") as send_message:
            #-------------------------------------------------------------------
            # Test controller events
            #-------------------------------------------------------------------
            project = Project('project', None, ['spider1', 'spider2'])
            protocol.on_controller_event(ControllerEvent.PROJECT_PUSH,
                                         project)
            protocol.on_controller_event(ControllerEvent.PROJECT_REMOVE,
                                         'project')

            #-------------------------------------------------------------------
            # Test PROJECT_REMOVE_ACTION
            #-------------------------------------------------------------------
            msg = {
                'type': 'ACTION',
                'action': 'PROJECT_REMOVE',
                'id': 'foo'
            }
            data = json_encode(msg)
            protocol.onMessage(data, False)

            msg['name'] = 'foo'
            data = json_encode(msg)
            protocol.onMessage(data, False)

            controller.remove_project.side_effect = ValueError('foo')
            protocol.onMessage(data, False)

            #-------------------------------------------------------------------
            # Test PROJECT_PUSH
            #-------------------------------------------------------------------
            d = Deferred()
            send_message.side_effect = make_deferred_func(d)
            msg = {
                'type': 'ACTION',
                'action': 'PROJECT_PUSH',
                'id': 'foo'
            }
            data = json_encode(msg)
            protocol.onMessage(data, False)
            yield d

            msg['archiveData'] = 'foo'
            data = json_encode(msg)
            d = Deferred()
            send_message.side_effect = make_deferred_func(d)
            protocol.onMessage(data, False)
            yield d

            msg['archiveData'] = base64.b64encode(b'foo').decode('utf-8')
            controller.push_project.return_value = Project('foo', None, [])
            data = json_encode(msg)
            d = Deferred()
            send_message.side_effect = make_deferred_func(d)
            protocol.onMessage(data, False)
            yield d

    #---------------------------------------------------------------------------
    def test_job_handling(self):
        protocol = self.protocol
        controller = self.controller

        #-----------------------------------------------------------------------
        # Test building of job dictionaries
        #-----------------------------------------------------------------------
        controller.get_job_logs.return_value = ('/foo/bar', '/foo/bar')
        job = Job(status=Status.CANCELED, actor=Actor.USER)
        job_dict = protocol.process_job(job)
        self.assertTrue(job_dict['outLog'])
        self.assertTrue(job_dict['errLog'])
