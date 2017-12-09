#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   27.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import json

from twisted.internet.defer import Deferred, inlineCallbacks
from scrapy_do.webservice import Status, PushProject, ListProjects, ListSpiders
from scrapy_do.webservice import ScheduleJob, ListJobs, CancelJob
from twisted.web.server import NOT_DONE_YET
from scrapy_do.schedule import Job, Actor
from scrapy_do.schedule import Status as JobStatus
from unittest.mock import Mock
from twisted.trial import unittest


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
        self.web_app.controller.get_job.return_value = self.job1
        self.web_app.controller.get_jobs.return_value = [self.job2]

    #---------------------------------------------------------------------------
    def test_status(self):
        service = Status(self.web_app)
        request = Mock()
        request.method = 'GET'
        retval = service.render(request)
        decoded = json.loads(retval)
        self.assertIn('memory-usage', decoded)
        self.assertIn('cpu-usage', decoded)

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
        request.args = {
            b'name': [b'test'],
            b'archive': [b'somedata']
        }
        web_app.controller.push_project.side_effect = None
        web_app.controller.push_project.return_value = ['test1', 'test2']

        service.render(request)
        yield d

        data = request.write.call_args[0][0].decode('utf-8')
        decoded = json.loads(data)
        self.assertIn('status', decoded)
        self.assertIn('spiders', decoded)
        self.assertEqual(decoded['status'], 'ok')
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
        request = Mock()
        request.method = 'POST'
        request.args = {
            b'project': [b'quotesbot'],
            b'spider': [b'toscrap-css'],
            b'when': [b'now']
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
        request.args = {b'id': [self.job1.identifier.encode('utf-8')]}
        retval = service.render(request)
        decoded = json.loads(retval)
        self.assertIn('status', decoded)
        self.assertIn('jobs', decoded)
        self.assertEqual(decoded['status'], 'ok')
        jobs = decoded['jobs']
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['identifier'], self.job1.identifier)
        self.assertEqual(jobs[0]['schedule'], self.job1.schedule)

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
