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
from scrapy_do.schedule import Status
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
        self.controller = Controller(self.config)

    #---------------------------------------------------------------------------
    def test_setup(self):
        Controller(self.config)  # no metadata file
        Controller(self.config)  # metadata file exists

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
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
