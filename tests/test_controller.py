#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   05.12.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import tempfile
import shutil
import os

from twisted.internet.defer import inlineCallbacks
from scrapy_do.controller import Controller
from scrapy_do.schedule import Status, Actor, Job
from scrapy_do.utils import twisted_sleep, run_process
from unittest.mock import Mock, patch, DEFAULT
from twisted.trial import unittest


#-------------------------------------------------------------------------------
class ControllerTests(unittest.TestCase):

    #---------------------------------------------------------------------------
    def setUp(self):
        with open('tests/quotesbot.zip', 'rb') as f:
            self.project_archive_data = f.read()

        self.temp_dir = tempfile.mkdtemp()
        self.config = Mock()
        self.config.get_string.return_value = self.temp_dir
        self.config.get_int.return_value = 2
        self.controller = Controller(self.config)

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def test_setup(self):
        #-----------------------------------------------------------------------
        # Set up the controller. Artificially add some RUNNING jobs to the
        # schedule to simulate the daemon being killed unexpectedly. These
        # jobs should be converted to PENDING to be restarted ASAP.
        #-----------------------------------------------------------------------
        controller = self.controller
        yield controller.push_project('quotesbot', self.project_archive_data)
        controller.schedule_job('quotesbot', 'toscrape-css', 'every second')
        controller.schedule_job('quotesbot', 'toscrape-xpath',
                                'every 2 seconds')

        job = Job(Status.RUNNING, Actor.SCHEDULER, 'now', 'foo1', 'bar1')
        self.controller.schedule.add_job(job)
        job = Job(Status.RUNNING, Actor.SCHEDULER, 'now', 'foo2', 'bar2')
        self.controller.schedule.add_job(job)
        self.assertEqual(len(controller.get_jobs(Status.RUNNING)), 2)

        #-----------------------------------------------------------------------
        # Set up another controller with the same config to see if the state
        # is reconstructed
        #-----------------------------------------------------------------------
        controller = Controller(self.config)
        self.assertEqual(len(controller.scheduler.jobs), 2)
        self.assertEqual(len(controller.get_jobs(Status.PENDING)), 2)

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def test_push_project(self):
        #-----------------------------------------------------------------------
        # Set up
        #-----------------------------------------------------------------------
        with open('tests/broken-proj.zip', 'rb') as f:
            broken_data = f.read()

        controller = self.controller

        #-----------------------------------------------------------------------
        # Configure the error cases tests
        #-----------------------------------------------------------------------
        def chk_unzip(e):
            self.assertEqual(str(e), 'Not a valid zip archive')
        unzip_error = {
            'name': 'test',
            'data': b'foo',
            'exc_check': chk_unzip
        }

        def chk_name(e):
            self.assertTrue(str(e).startswith('Project'))
        name_error = {
            'name': 'test',
            'data': broken_data,
            'exc_check': chk_name
        }

        def chk_list(e):
            self.assertEqual(str(e), 'Unable to get the list of spiders')
        list_error = {
            'name': 'broken-proj',
            'data': broken_data,
            'exc_check': chk_list
        }

        error_params = [unzip_error, name_error, list_error]

        #-----------------------------------------------------------------------
        # Test the error cases
        #-----------------------------------------------------------------------
        for params in error_params:
            temp_test_dir = tempfile.mkdtemp()
            temp_test_file = tempfile.mkstemp()
            with patch.multiple('tempfile',
                                mkstemp=DEFAULT, mkdtemp=DEFAULT) as mock:
                mock['mkdtemp'].return_value = temp_test_dir
                mock['mkstemp'].return_value = temp_test_file

                try:
                    yield controller.push_project(params['name'],
                                                  params['data'])
                    self.assertFail()
                except ValueError as e:
                    params['exc_check'](e)

                self.assertFalse(os.path.exists(temp_test_dir))
                self.assertFalse(os.path.exists(temp_test_file[1]))

        #-----------------------------------------------------------------------
        # Test the correct case
        #-----------------------------------------------------------------------
        temp_test_dir = tempfile.mkdtemp()
        temp_test_file = tempfile.mkstemp()
        with patch.multiple('tempfile',
                            mkstemp=DEFAULT, mkdtemp=DEFAULT) as mock:
            mock['mkdtemp'].return_value = temp_test_dir
            mock['mkstemp'].return_value = temp_test_file

            spiders = yield controller.push_project('quotesbot',
                                                    self.project_archive_data)
            self.assertFalse(os.path.exists(temp_test_dir))
            self.assertFalse(os.path.exists(temp_test_file[1]))
            self.assertIn('toscrape-css', spiders)
            self.assertIn('toscrape-xpath', spiders)

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def test_accessors_mutators(self):
        #-----------------------------------------------------------------------
        # Set up
        #-----------------------------------------------------------------------
        controller = self.controller
        spiders_p = yield controller.push_project('quotesbot',
                                                  self.project_archive_data)
        self.assertIn('toscrape-css', spiders_p)
        self.assertIn('toscrape-xpath', spiders_p)

        #-----------------------------------------------------------------------
        # Project/spider accessors
        #-----------------------------------------------------------------------
        projects = controller.get_projects()
        self.assertIn('quotesbot', projects)
        spiders = controller.get_spiders('quotesbot')
        for spider in spiders_p:
            self.assertIn(spider, spiders)

        self.assertRaises(KeyError,
                          f=controller.get_spiders,
                          project_name='foo')

        #-----------------------------------------------------------------------
        # Job scheduling
        #-----------------------------------------------------------------------
        self.assertRaises(KeyError,
                          f=controller.schedule_job,
                          project='foo', spider='bar', when='bar')
        self.assertRaises(KeyError,
                          f=controller.schedule_job,
                          project='quotesbot', spider='bar', when='bar')

        job1_id = controller.schedule_job('quotesbot', 'toscrape-css',
                                          'every 25 minutes')
        job2_id = controller.schedule_job('quotesbot', 'toscrape-xpath', 'now')
        job3_id = controller.schedule_job('quotesbot', 'toscrape-css', 'now')

        #-----------------------------------------------------------------------
        # Retrieve the jobs
        #-----------------------------------------------------------------------
        job1 = controller.get_job(job1_id)
        job2 = controller.get_job(job2_id)
        job3 = controller.get_job(job3_id)

        self.assertEqual(job1.identifier, job1_id)
        self.assertEqual(job2.identifier, job2_id)
        self.assertEqual(job3.identifier, job3_id)
        self.assertEqual(job1.status, Status.SCHEDULED)
        self.assertEqual(job2.status, Status.PENDING)
        self.assertEqual(job3.status, Status.PENDING)

        scheduled_jobs = controller.get_jobs(Status.SCHEDULED)
        pending_jobs = controller.get_jobs(Status.PENDING)
        self.assertEqual(len(scheduled_jobs), 1)
        self.assertEqual(len(pending_jobs), 2)

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def test_run_scheduler(self):
        #-----------------------------------------------------------------------
        # Set up
        #-----------------------------------------------------------------------
        controller = self.controller
        spiders_p = yield controller.push_project('quotesbot',
                                                  self.project_archive_data)
        self.assertIn('toscrape-css', spiders_p)
        self.assertIn('toscrape-xpath', spiders_p)

        #-----------------------------------------------------------------------
        # Check if a scheduled job created a new pending job after two
        # seconds
        #-----------------------------------------------------------------------
        job_id = controller.schedule_job('quotesbot', 'toscrape-css',
                                         'every second')
        yield twisted_sleep(2)
        controller.run_scheduler()

        pending_jobs = controller.get_jobs(Status.PENDING)
        job_s = controller.get_job(job_id)
        job_p = pending_jobs[0]
        self.assertEqual(len(pending_jobs), 1)
        self.assertEqual(job_p.project, job_s.project)
        self.assertEqual(job_p.spider, job_s.spider)
        self.assertEqual(job_p.actor, Actor.SCHEDULER)
        self.assertEqual(job_p.status, Status.PENDING)

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def test_run_process(self):
        temp_dir = tempfile.mkdtemp()
        out_path = os.path.join(temp_dir, 'foo' + '.out')
        err_path = os.path.join(temp_dir, 'foo' + '.err')
        process, exit_status = run_process('cat', ['/etc/group'], 'foo',
                                           temp_dir)
        status = yield exit_status
        self.assertEqual(status, 0)
        self.assertTrue(os.path.exists(out_path))
        self.assertFalse(os.path.exists(err_path))

        process, exit_status = run_process('cat', ['/dev/null'], 'foo',
                                           temp_dir)
        status = yield exit_status
        self.assertEqual(status, 0)
        self.assertFalse(os.path.exists(out_path))
        self.assertFalse(os.path.exists(err_path))

        shutil.rmtree(temp_dir)

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def test_run_crawler(self):
        #-----------------------------------------------------------------------
        # Test the successfull case
        #-----------------------------------------------------------------------
        controller = self.controller
        yield controller.push_project('quotesbot', self.project_archive_data)
        temp_dir = tempfile.mkdtemp()

        with patch('tempfile.mkdtemp') as mock_mkdtemp:
            mock_mkdtemp.return_value = temp_dir
            _, finished = yield controller._run_crawler('quotesbot',
                                                        'toscrape-css', 'foo')

        status = yield finished
        self.assertEqual(status, 0)
        self.assertFalse(os.path.exists(temp_dir))
        log_file = os.path.join(controller.log_dir, 'foo.err')
        self.assertTrue(os.path.exists(log_file))

        #-----------------------------------------------------------------------
        # Test the unzipping failuer
        #-----------------------------------------------------------------------
        try:
            yield controller._run_crawler('foo', 'bar', 'foo')
            self.fail('Unzipping a non-existent archive should have risen '
                      'an IOError')
        except IOError as e:
            self.assertEquals(str(e), 'Cannot unzip the project archive')

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def test_run_crawlers(self):
        #-----------------------------------------------------------------------
        # Set the projects up, schedule some jobs, and run the scheduler
        #-----------------------------------------------------------------------
        controller = self.controller
        yield controller.push_project('quotesbot', self.project_archive_data)
        controller.schedule_job('quotesbot', 'toscrape-css', 'every second')
        controller.schedule_job('quotesbot', 'toscrape-xpath', 'every second')
        controller.schedule_job('quotesbot', 'toscrape-css', 'every second')
        controller.schedule_job('quotesbot', 'toscrape-xpath', 'every second')

        yield twisted_sleep(2)
        controller.run_scheduler()
        pending_jobs = controller.get_jobs(Status.PENDING)
        self.assertEqual(len(pending_jobs), 4)

        #-----------------------------------------------------------------------
        # Run the crawlers
        #-----------------------------------------------------------------------
        controller.run_crawlers()

        running_jobs = controller.get_jobs(Status.RUNNING)
        pending_jobs = controller.get_jobs(Status.PENDING)
        self.assertEqual(len(running_jobs), 2)
        self.assertEqual(len(pending_jobs), 2)

        yield controller.wait_for_running_jobs()
        controller.run_crawlers()
        yield controller.wait_for_running_jobs()

        pending_jobs = controller.get_jobs(Status.PENDING)
        successful_jobs = controller.get_jobs(Status.SUCCESSFUL)
        self.assertEqual(len(successful_jobs), 4)
        self.assertEqual(len(pending_jobs), 0)

        for job in successful_jobs:
            log_file = os.path.join(self.temp_dir, 'log-dir',
                                    successful_jobs[0].identifier + '.err')
            self.assertTrue(os.path.exists(log_file))

        #-----------------------------------------------------------------------
        # Test failure to spawn a job
        #-----------------------------------------------------------------------
        job = Job(Status.PENDING, Actor.SCHEDULER, 'now', 'foo', 'bar')
        self.controller.schedule.add_job(job)
        controller.run_crawlers()
        yield controller.wait_for_starting_jobs()
        job = controller.get_job(job.identifier)
        self.assertEqual(job.status, Status.FAILED)

        #-----------------------------------------------------------------------
        # Spawn a job but then kill it
        #-----------------------------------------------------------------------
        controller.schedule_job('quotesbot', 'toscrape-css', 'now')
        controller.run_crawlers()
        yield controller.wait_for_running_jobs(cancel=True)

    #---------------------------------------------------------------------------
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
