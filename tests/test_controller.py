#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   05.12.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import tempfile
import shutil
import uuid
import json
import os

from twisted.internet.defer import inlineCallbacks
from scrapy_do.controller import Controller
from scrapy_do.schedule import Status, Actor, Job
from scrapy_do.utils import twisted_sleep, run_process
from distutils.spawn import find_executable
from unittest.mock import Mock, patch, DEFAULT
from twisted.trial import unittest


#-------------------------------------------------------------------------------
class ControllerTests(unittest.TestCase):

    #---------------------------------------------------------------------------
    def setUp(self):
        with open('tests/quotesbot.zip', 'rb') as f:
            self.project_archive_data = f.read()

        with open('tests/quotesbot-no-css.zip', 'rb') as f:
            self.project_no_css_archive_data = f.read()

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
        yield controller.push_project(self.project_archive_data)
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
        yield twisted_sleep(3)
        controller.run_scheduler()
        pending_jobs = controller.get_jobs(Status.PENDING)
        pending_spiders = [job.spider for job in pending_jobs]
        self.assertEqual(len(pending_jobs), 4)

        for spider in ['toscrape-css', 'toscrape-xpath', 'bar1', 'bar2']:
            self.assertIn(spider, pending_spiders)

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def test_push_project(self):
        #-----------------------------------------------------------------------
        # Set up
        #-----------------------------------------------------------------------
        with open('tests/broken-no-proj.zip', 'rb') as f:
            broken_data_no_proj = f.read()

        with open('tests/broken-no-name.zip', 'rb') as f:
            broken_data_no_name = f.read()

        with open('tests/broken-wrong-name.zip', 'rb') as f:
            broken_data_wrong_name = f.read()

        with open('tests/broken-no-spiders.zip', 'rb') as f:
            broken_data_no_spiders = f.read()

        controller = self.controller

        #-----------------------------------------------------------------------
        # Configure the error cases tests
        #-----------------------------------------------------------------------
        def chk_unzip(e):
            self.assertEqual(str(e), 'Not a valid zip archive')
        unzip_error = {
            'data': b'foo',
            'exc_check': chk_unzip
        }

        def chk_prj(e):
            self.assertEqual(str(e), 'No project found in the archive')
        no_project_error = {
            'data': broken_data_no_proj,
            'exc_check': chk_prj
        }

        def chk_name_exists(e):
            self.assertEqual(str(e),
                             'Can\'t extract project name from the config file')
        no_name_error = {
            'data': broken_data_no_name,
            'exc_check': chk_name_exists
        }

        def chk_name(e):
            self.assertTrue(str(e).startswith('Project'))
        wrong_name_error = {
            'data': broken_data_wrong_name,
            'exc_check': chk_name
        }

        def chk_list(e):
            self.assertEqual(str(e), 'Unable to get the list of spiders')
        list_error = {
            'data': broken_data_no_spiders,
            'exc_check': chk_list
        }

        error_params = [
            unzip_error, no_project_error, no_name_error, wrong_name_error,
            list_error
        ]

        #-----------------------------------------------------------------------
        # Test the error cases
        #-----------------------------------------------------------------------
        unzip = find_executable('unzip')
        scrapy = find_executable('scrapy')
        for params in error_params:
            temp_test_dir = tempfile.mkdtemp()
            temp_test_file = tempfile.mkstemp()
            with patch.multiple('tempfile',
                                mkstemp=DEFAULT, mkdtemp=DEFAULT) as mock:
                mock['mkdtemp'].return_value = temp_test_dir
                mock['mkstemp'].return_value = temp_test_file
                with patch('scrapy_do.controller.find_executable') as fe_mock:
                    fe_mock.side_effect = [unzip, '/bin/false']
                    try:
                        yield controller.push_project(params['data'])
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

            project = yield controller.push_project(self.project_archive_data)
            self.assertFalse(os.path.exists(temp_test_dir))
            self.assertFalse(os.path.exists(temp_test_file[1]))
            self.assertEqual('quotesbot', project.name)
            self.assertIn('toscrape-css', project.spiders)
            self.assertIn('toscrape-xpath', project.spiders)

        #-----------------------------------------------------------------------
        # Schedule a job for one of the spiders and remove it in the new
        # archive
        #-----------------------------------------------------------------------
        controller.schedule_job('quotesbot', 'toscrape-css', 'every 25 minutes')
        try:
            yield controller.push_project(self.project_no_css_archive_data)
            self.fail('Inserting a project without a spider having scheduled '
                      'jobs should fail')
        except ValueError as e:
            self.assertTrue(str(e).startswith('Spider toscrape-css'))

        yield controller.push_project(self.project_archive_data)

        #-----------------------------------------------------------------------
        # Test missing executables
        #-----------------------------------------------------------------------
        side_effects = [
            ([None, scrapy], 'Please install unzip'),
            ([unzip, None], 'Please install scrapy')
        ]
        for se, msg in side_effects:
            with patch('scrapy_do.controller.find_executable') as fe_mock:
                fe_mock.side_effect = se
                try:
                    yield controller.push_project(self.project_archive_data)
                    self.fail('Pusing projects without required executables'
                              ' should have risen an EnvironmentError')
                except EnvironmentError as e:
                    self.assertTrue(str(e).startswith(msg))

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def test_accessors_mutators(self):
        #-----------------------------------------------------------------------
        # Set up
        #-----------------------------------------------------------------------
        controller = self.controller
        project = yield controller.push_project(self.project_archive_data)
        self.assertIn('toscrape-css', project.spiders)
        self.assertIn('toscrape-xpath', project.spiders)

        #-----------------------------------------------------------------------
        # Project/spider accessors
        #-----------------------------------------------------------------------
        projects = controller.get_projects()
        self.assertIn('quotesbot', projects)
        spiders = controller.get_spiders('quotesbot')
        for spider in project.spiders:
            self.assertIn(spider, spiders)

        self.assertRaises(ValueError,
                          f=controller.get_spiders,
                          project_name='foo')

        #-----------------------------------------------------------------------
        # Job scheduling
        #-----------------------------------------------------------------------
        self.assertRaises(ValueError,
                          f=controller.schedule_job,
                          project='foo', spider='bar', when='bar')
        self.assertRaises(ValueError,
                          f=controller.schedule_job,
                          project='quotesbot', spider='bar', when='bar')

        job1_id = controller.schedule_job('quotesbot', 'toscrape-css',
                                          'every 25 minutes')
        job2_id = controller.schedule_job('quotesbot', 'toscrape-xpath', 'now')
        job3_id = controller.schedule_job('quotesbot', 'toscrape-css', 'now',
                                          payload='{}')

        try:
            controller.schedule_job('quotesbot', 'toscrape-css', 'now',
                                    payload="foo")
            self.assertFail()
        except ValueError as e:
            self.assertTrue(str(e).startswith('Payload is not a valid JSON'))

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
        project = yield controller.push_project(self.project_archive_data)
        self.assertIn('toscrape-css', project.spiders)
        self.assertIn('toscrape-xpath', project.spiders)

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
        yield controller.push_project(self.project_archive_data)
        temp_dir = tempfile.mkdtemp()

        payload = {
            'test1': str(uuid.uuid4()),
            'test2': [str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())],
            'test3': 1234567890
        }

        with patch('tempfile.mkdtemp') as mock_mkdtemp:
            mock_mkdtemp.return_value = temp_dir
            _, finished = yield controller._run_crawler('quotesbot',
                                                        'toscrape-css', 'foo',
                                                        json.dumps(payload))

        status = yield finished
        self.assertEqual(status, 0)
        self.assertFalse(os.path.exists(temp_dir))
        err_file = os.path.join(controller.log_dir, 'foo.err')
        self.assertTrue(os.path.exists(err_file))
        out_file = os.path.join(controller.log_dir, 'foo.out')
        with open(out_file, 'rb') as f:
            contents = f.read().decode('utf-8')
            self.assertIn(payload['test1'], contents)
            for id in payload['test2']:
                self.assertIn(id, contents)
            self.assertIn(str(payload['test3']), contents)

        #-----------------------------------------------------------------------
        # Unzip not found
        #-----------------------------------------------------------------------
        with patch('scrapy_do.controller.find_executable') as fe_mock:
            fe_mock.side_effect = [None]
            try:
                yield controller._run_crawler('foo', 'bar', 'foo', '{}')
                self.fail('Unzipping a without unzip should have risen '
                          'an EnvironmentError')
            except EnvironmentError as e:
                self.assertTrue(str(e).startswith('Please install unzip'))

        #-----------------------------------------------------------------------
        # Test the unzipping failuer
        #-----------------------------------------------------------------------
        try:
            yield controller._run_crawler('foo', 'bar', 'foo', '{}')
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
        yield controller.push_project(self.project_archive_data)
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
        # Test the log getter
        #-----------------------------------------------------------------------
        for job in successful_jobs:
            log = controller.get_job_logs(job.identifier)
            if job.spider == 'toscrape-css':
                self.assertNotEqual(log[0], None)
            else:
                self.assertEqual(log[0], None)
            self.assertNotEqual(log[1], None)

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

        #-----------------------------------------------------------------------
        # Check the overall number of completed and active jobs
        #-----------------------------------------------------------------------
        self.assertEqual(len(controller.get_active_jobs()), 4)
        self.assertEqual(len(controller.get_completed_jobs()), 6)

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def test_cancel(self):
        #-----------------------------------------------------------------------
        # Set things up
        #-----------------------------------------------------------------------
        controller = self.controller
        yield controller.push_project(self.project_archive_data)
        job_id1 = controller.schedule_job('quotesbot', 'toscrape-css',
                                          'every second')
        controller.schedule_job('quotesbot', 'toscrape-xpath', 'every second')
        controller.schedule_job('quotesbot', 'toscrape-css', 'every second')
        controller.schedule_job('quotesbot', 'toscrape-xpath', 'every second')

        #-----------------------------------------------------------------------
        # Cancel a scheduled job
        #-----------------------------------------------------------------------
        yield controller.cancel_job(job_id1)
        job = controller.get_job(job_id1)
        self.assertEqual(job.status, Status.CANCELED)

        #-----------------------------------------------------------------------
        # Convert the remaining scheduled jobs to pending jobs
        #-----------------------------------------------------------------------
        yield twisted_sleep(2)
        controller.run_scheduler()
        pending_jobs = controller.get_jobs(Status.PENDING)
        self.assertEqual(len(pending_jobs), 3)
        job_ids = [x.identifier for x in pending_jobs]
        job_id2, job_id3, job_id4 = job_ids

        #-----------------------------------------------------------------------
        # Cancel a pending job
        #-----------------------------------------------------------------------
        yield controller.cancel_job(job_id2)
        job = controller.get_job(job_id2)
        self.assertEqual(job.status, Status.CANCELED)

        #-----------------------------------------------------------------------
        # Run the remaining pending jobs and cancel one of them. Start the
        # cancellation early to test the case when the job process haven't
        # had enough time to start.
        #-----------------------------------------------------------------------
        controller.run_crawlers()
        cancel_done = controller.cancel_job(job_id3)
        yield controller.wait_for_starting_jobs()
        yield cancel_done

        #-----------------------------------------------------------------------
        # Temporarily remove a job from a dictionary to simulate a race
        # condition in which the job finishes while the canceling procedure
        # sleeps waiting for the process to start
        #-----------------------------------------------------------------------
        job_data4 = controller.running_jobs[job_id4]
        del controller.running_jobs[job_id4]  # this simulates the race

        try:
            yield controller.cancel_job(job_id4)
            self.fail('Cancelling a job missing from the dictionary should '
                      'have risen a ValueError exception but did not')
        except ValueError:
            pass

        controller.running_jobs[job_id4] = job_data4
        yield controller.wait_for_running_jobs()

        #-----------------------------------------------------------------------
        # Cancel an inactive job
        #-----------------------------------------------------------------------
        try:
            yield controller.cancel_job(job_id4)
            self.fail('Cancelling an incactive job should have risen '
                      'a ValueError exception but did not')
        except ValueError:
            pass

        #-----------------------------------------------------------------------
        # Check the final statuses
        #-----------------------------------------------------------------------
        self.assertEqual(controller.get_job(job_id1).status, Status.CANCELED)
        self.assertEqual(controller.get_job(job_id2).status, Status.CANCELED)
        self.assertEqual(controller.get_job(job_id3).status, Status.CANCELED)
        self.assertEqual(controller.get_job(job_id4).status, Status.SUCCESSFUL)

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def test_purge_completed(self):
        controller = self.controller
        yield controller.push_project(self.project_archive_data)
        controller.schedule_job('quotesbot', 'toscrape-css', 'every second')
        controller.schedule_job('quotesbot', 'toscrape-xpath', 'every second')
        controller.schedule_job('quotesbot', 'toscrape-css', 'every second')
        controller.schedule_job('quotesbot', 'toscrape-xpath', 'every second')

        yield twisted_sleep(2)
        controller.run_scheduler()

        for _ in range(2):
            controller.run_crawlers()
            yield controller.wait_for_running_jobs()

        completed_jobs = controller.get_completed_jobs()
        self.assertEqual(len(completed_jobs), 4)
        controller.purge_completed_jobs()
        self.assertEqual(len(controller.get_completed_jobs()), 2)
        for job in completed_jobs[2:]:
            log_file = os.path.join(controller.log_dir, job.identifier + '.err')
            self.assertFalse(os.path.exists(log_file))

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def test_remove_project(self):
        controller = self.controller
        yield controller.push_project(self.project_archive_data)
        id1 = controller.schedule_job('quotesbot', 'toscrape-css',
                                      'every second')
        id2 = controller.schedule_job('quotesbot', 'toscrape-xpath',
                                      'every second')

        try:
            controller.remove_project('foo')
            self.fail('Removing a non-existent project risen an exception')
        except ValueError as e:
            self.assertTrue(str(e).startswith("No such project"))

        try:
            controller.remove_project('quotesbot')
            self.fail('Removing a project with scheduled spiders should have '
                      'risen an exception')
        except ValueError as e:
            self.assertTrue(str(e).startswith('There are 2'))

        yield controller.cancel_job(id1)
        yield controller.cancel_job(id2)

        controller.remove_project('quotesbot')
        self.assertEqual(len(controller.projects), 0)

    #---------------------------------------------------------------------------
    def test_events(self):
        controller = self.controller
        listener = Mock()
        controller.add_event_listener(listener)
        controller.dispatch_periodic_events()
        controller.remove_event_listener(listener)

    #---------------------------------------------------------------------------
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
