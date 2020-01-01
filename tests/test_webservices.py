#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   27.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import json
import uuid

from twisted.internet.defer import Deferred, inlineCallbacks
from scrapy_do.webservice import Status, PushProject, ListProjects, ListSpiders
from scrapy_do.webservice import ScheduleJob, ListJobs, CancelJob, RemoveProject
from scrapy_do.webservice import WebApp
from scrapy_do.controller import Project
from twisted.web.server import NOT_DONE_YET
from scrapy_do.schedule import Job, Actor
from scrapy_do.schedule import Status as JobStatus
from unittest.mock import Mock, patch
from twisted.trial import unittest
from datetime import datetime


#-------------------------------------------------------------------------------
class WebServicesTests(unittest.TestCase):

    #---------------------------------------------------------------------------
    def setUp(self):
        self.web_app = Mock()
        self.web_app.controller.get_projects.return_value = ['quotesbot']

        #-----------------------------------------------------------------------
        # Projects
        #-----------------------------------------------------------------------
        self.spiders = ['toscrape-css', 'toscrape-xpath']

        def get_spiders(project_name):
            if project_name == 'quotesbot':
                return self.spiders
            raise KeyError('No such project')
        self.web_app.controller.get_spiders.side_effect = get_spiders

        #-----------------------------------------------------------------------
        # Jobs
        #-----------------------------------------------------------------------
        self.web_app.controller.schedule_job.return_value = 'foo'
        self.job1 = Job(JobStatus.PENDING, Actor.SCHEDULER,
                        schedule='every 5 minutes', project='quotesbot',
                        spider='toscrape-xpath')
        self.job2 = Job(JobStatus.SCHEDULED, Actor.USER, schedule='now',
                        project='quotesbot', spider='toscrape-css')
        self.job3 = Job(JobStatus.CANCELED, Actor.SCHEDULER,
                        schedule='now', project='quotesbot',
                        spider='toscrape-xpath')
        self.job4 = Job(JobStatus.SUCCESSFUL, Actor.USER, schedule='now',
                        project='quotesbot', spider='toscrape-css')
        self.web_app.controller.get_job.return_value = self.job1
        self.web_app.controller.get_jobs.return_value = [self.job2]
        active_jobs = [self.job1, self.job2]
        done_jobs = [self.job3, self.job4]
        self.web_app.controller.get_active_jobs.return_value = active_jobs
        self.web_app.controller.get_completed_jobs.return_value = done_jobs
        self.web_app.controller.start_time = datetime.now()
        self.web_app.controller.counter_run = 0
        self.web_app.controller.counter_success = 0
        self.web_app.controller.counter_failure = 0
        self.web_app.controller.counter_cancel = 0
        self.web_app.controller.scheduled_jobs = []
        prj1 = Project('a', 'a.zip', ['a', 'b'])
        prj2 = Project('b', 'b.zip', ['c'])
        self.web_app.controller.projects = {
            'prj1': prj1,
            'prj2': prj2
        }

    #---------------------------------------------------------------------------
    def test_status(self):
        service = Status(self.web_app)
        request = Mock()
        request.method = 'GET'
        retval = service.render(request)
        decoded = json.loads(retval)
        keys = ['memory-usage', 'cpu-usage', 'time', 'timezone', 'hostname',
                'uptime', 'jobs-run', 'jobs-successful', 'jobs-failed',
                'jobs-canceled', 'jobs-scheduled', 'projects', 'spiders',
                'daemon-version']
        for key in keys:
            self.assertIn(key, decoded)

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def test_push_project(self):
        #-----------------------------------------------------------------------
        # Set the resource up
        #-----------------------------------------------------------------------
        web_app = Mock()
        web_app.controller = Mock()
        request = Mock()
        request.args = {}
        request.method = 'POST'
        service = PushProject(web_app)

        #-----------------------------------------------------------------------
        # Test wrong params
        #-----------------------------------------------------------------------
        d = Deferred()
        request.finish.side_effect = lambda: d.callback(None)

        ret = service.render(request)
        yield d

        code = request.setResponseCode.call_args[0][0]
        headers = request.setHeader.call_args_list
        data = request.write.call_args[0][0].decode('utf-8')
        decoded = json.loads(data)

        self.assertEqual(ret, NOT_DONE_YET)
        self.assertEqual(code, 400)
        self.assertIn((('Content-Type', 'application/json'),), headers)
        self.assertIn('status', decoded)
        self.assertEqual(decoded['status'], 'error')

        #-----------------------------------------------------------------------
        # Test controller error
        #-----------------------------------------------------------------------
        request.reset_mock()
        d = Deferred()
        request.finish.side_effect = lambda: d.callback(None)
        request.args = {
            b'name': [b'test'],
            b'archive': [b'somedata']
        }
        web_app.controller.push_project.side_effect = ValueError('error')

        service.render(request)
        yield d

        code = request.setResponseCode.call_args[0][0]
        data = request.write.call_args[0][0].decode('utf-8')
        decoded = json.loads(data)

        self.assertEqual(code, 400)
        self.assertIn('status', decoded)
        self.assertEqual(decoded['status'], 'error')

        #-----------------------------------------------------------------------
        # Controller success
        #-----------------------------------------------------------------------
        request.reset_mock()
        web_app.controller.reset_mock()
        d = Deferred()
        request.finish.side_effect = lambda: d.callback(None)
        request.args = {b'archive': [b'somedata']}
        web_app.controller.push_project.side_effect = None
        web_app.controller.push_project.return_value = \
            Project('test', None, ['test1', 'test2'])

        service.render(request)
        yield d

        data = request.write.call_args[0][0].decode('utf-8')
        decoded = json.loads(data)
        self.assertIn('status', decoded)
        self.assertIn('name', decoded)
        self.assertIn('spiders', decoded)
        self.assertEqual(decoded['status'], 'ok')
        self.assertEqual(decoded['name'], 'test')
        self.assertIn('test1', decoded['spiders'])
        self.assertIn('test2', decoded['spiders'])

    #---------------------------------------------------------------------------
    def test_list_projects(self):
        service = ListProjects(self.web_app)
        request = Mock()
        request.method = 'GET'
        retval = service.render(request)
        decoded = json.loads(retval)
        self.assertIn('status', decoded)
        self.assertIn('projects', decoded)
        self.assertIn('quotesbot', decoded['projects'])

    #---------------------------------------------------------------------------
    def test_list_spiders(self):
        #-----------------------------------------------------------------------
        # List spiders - bad parameter name
        #-----------------------------------------------------------------------
        service = ListSpiders(self.web_app)
        request = Mock()
        request.method = 'GET'
        request.args = {b'proj': [b'']}
        retval = service.render(request)
        decoded = json.loads(retval)

        self.assertIn('status', decoded)
        self.assertIn('msg', decoded)
        self.assertEqual(decoded['status'], 'error')
        self.assertTrue(decoded['msg'].startswith("'Missing argument"))

        #-----------------------------------------------------------------------
        # List spiders - valid
        #-----------------------------------------------------------------------
        request.args = {b'project': [b'quotesbot']}
        retval = service.render(request)
        decoded = json.loads(retval)

        self.assertIn('status', decoded)
        self.assertIn('project', decoded)
        self.assertIn('spiders', decoded)
        for spider in self.spiders:
            self.assertIn(spider, decoded['spiders'])
        self.assertEqual(decoded['status'], 'ok')
        self.assertEqual(decoded['project'], 'quotesbot')

    #---------------------------------------------------------------------------
    def test_schedule_job(self):
        service = ScheduleJob(self.web_app)

        payload = {
            'test1': str(uuid.uuid4()),
            'test2': [str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())],
            'test3': 1234567890
        }

        request = Mock()
        request.method = 'POST'
        request.args = {
            b'project': [b'quotesbot'],
            b'spider': [b'toscrap-css'],
            b'when': [b'now'],
            b'description': [b'foo'],
            b'payload': [json.dumps(payload).encode('utf-8')]
        }
        retval = service.render(request)
        decoded = json.loads(retval)
        self.assertIn('status', decoded)
        self.assertIn('identifier', decoded)
        self.assertEqual(decoded['status'], 'ok')
        self.assertEqual(decoded['identifier'], 'foo')

    #---------------------------------------------------------------------------
    def test_list_jobs(self):
        #-----------------------------------------------------------------------
        # List jobs - missing parameters
        #-----------------------------------------------------------------------
        service = ListJobs(self.web_app)
        request = Mock()
        request.method = 'GET'
        request.args = {}
        retval = service.render(request)
        decoded = json.loads(retval)
        self.assertIn('status', decoded)
        self.assertIn('msg', decoded)
        self.assertEqual(decoded['status'], 'error')
        self.assertTrue(decoded['msg'].startswith("'Neither argument present"))

        #-----------------------------------------------------------------------
        # List jobs by id
        #-----------------------------------------------------------------------
        service = ListJobs(self.web_app)
        request = Mock()
        request.method = 'GET'
        job_id = self.job1.identifier
        request.args = {b'id': [job_id.encode('utf-8')]}
        retval = service.render(request)
        decoded = json.loads(retval)
        self.assertIn('status', decoded)
        self.assertIn('jobs', decoded)
        self.assertEqual(decoded['status'], 'ok')
        jobs = decoded['jobs']
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['identifier'], self.job1.identifier)
        self.assertEqual(jobs[0]['schedule'], self.job1.schedule)
        self.web_app.controller.get_job.assert_called_with(job_id)

        #-----------------------------------------------------------------------
        # List jobs by status
        #-----------------------------------------------------------------------
        service = ListJobs(self.web_app)
        request = Mock()
        request.method = 'GET'
        request.args = {b'status': ['PENDING'.encode('utf-8')]}
        retval = service.render(request)
        decoded = json.loads(retval)
        self.assertIn('status', decoded)
        self.assertIn('jobs', decoded)
        self.assertEqual(decoded['status'], 'ok')
        jobs = decoded['jobs']
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['identifier'], self.job2.identifier)
        self.assertEqual(jobs[0]['schedule'], self.job2.schedule)
        self.web_app.controller.get_jobs.assert_called_with(JobStatus.PENDING)

        #-----------------------------------------------------------------------
        # List active and completed jobs
        #-----------------------------------------------------------------------
        statuses = ['ACTIVE', 'COMPLETED']
        valid_statuses = [
            ['SCHEDULED', 'PENDING', 'RUNNING'],
            ['SUCCESSFUL', 'FAILED', 'CANCELED']
        ]
        num_jobs = [2, 2]

        for i in range(len(statuses)):
            service = ListJobs(self.web_app)
            request = Mock()
            request.method = 'GET'
            request.args = {b'status': [statuses[i].encode('utf-8')]}
            retval = service.render(request)
            decoded = json.loads(retval)
            self.assertIn('status', decoded)
            self.assertIn('jobs', decoded)
            self.assertEqual(decoded['status'], 'ok')
            jobs = decoded['jobs']
            self.assertEqual(len(jobs), num_jobs[i])
            for job in jobs:
                self.assertIn(job['status'], valid_statuses[i])

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def test_cancel_job(self):
        #-----------------------------------------------------------------------
        # Set the resource up
        #-----------------------------------------------------------------------
        web_app = Mock()
        web_app.controller = Mock()
        request = Mock()
        request.args = {}
        request.method = 'POST'
        service = CancelJob(web_app)

        #-----------------------------------------------------------------------
        # Test a missing param
        #-----------------------------------------------------------------------
        d = Deferred()
        request.finish.side_effect = lambda: d.callback(None)

        ret = service.render(request)
        yield d

        code = request.setResponseCode.call_args[0][0]
        headers = request.setHeader.call_args_list
        data = request.write.call_args[0][0].decode('utf-8')
        decoded = json.loads(data)

        self.assertEqual(ret, NOT_DONE_YET)
        self.assertEqual(code, 400)
        self.assertIn((('Content-Type', 'application/json'),), headers)
        self.assertIn('status', decoded)
        self.assertEqual(decoded['status'], 'error')

        #-----------------------------------------------------------------------
        # Test a controller error
        #-----------------------------------------------------------------------
        request.reset_mock()
        d = Deferred()
        request.finish.side_effect = lambda: d.callback(None)
        request.args = {b'id': [b'foo']}
        web_app.controller.cancel_job.side_effect = KeyError('error')

        service.render(request)
        yield d

        code = request.setResponseCode.call_args[0][0]
        data = request.write.call_args[0][0].decode('utf-8')
        decoded = json.loads(data)

        self.assertEqual(code, 400)
        self.assertIn('status', decoded)
        self.assertEqual(decoded['status'], 'error')

        #-----------------------------------------------------------------------
        # Controller success
        #-----------------------------------------------------------------------
        request.reset_mock()
        web_app.controller.reset_mock()
        d = Deferred()
        request.finish.side_effect = lambda: d.callback(None)
        request.args = {b'id': [b'foo']}
        web_app.controller.cancel_job.side_effect = None

        service.render(request)
        yield d

        data = request.write.call_args[0][0].decode('utf-8')
        decoded = json.loads(data)
        self.assertIn('status', decoded)
        self.assertEqual(decoded['status'], 'ok')

    #---------------------------------------------------------------------------
    def test_remove_project(self):
        #-----------------------------------------------------------------------
        # Set the resource up
        #-----------------------------------------------------------------------
        web_app = Mock()
        web_app.controller = Mock()
        request = Mock()
        request.args = {}
        request.method = 'POST'
        service = RemoveProject(web_app)
        request.args = {b'name': [b'foo']}
        data = service.render(request)
        decoded = json.loads(data)
        self.assertIn('status', decoded)
        self.assertEqual(decoded['status'], 'ok')

    #---------------------------------------------------------------------------
    def test_web_app(self):
        config = Mock()
        config.get_options.return_value = []
        controller = Mock()
        request = Mock()
        with patch('scrapy_do.webservice.get_data') as get_data:
            manifest_data = b'{"files": {"foo": "bar", "foo1": "/bar1"}}'
            get_data.return_value = manifest_data
            web_app = WebApp(config, controller)
        request.uri = b'/foo'
        index = web_app.getChild(None, request)
        self.assertEqual(index, web_app.index)
        request.uri = b'/favicon.png'
        favicon = web_app.getChild(None, request)
        self.assertNotEqual(favicon, web_app.index)
        self.assertEqual(favicon.render_GET(request),
                         b'{"files": {"foo": "bar", "foo1": "/bar1"}}')
