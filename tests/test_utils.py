#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   30.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import unittest
import schedule

from scrapy_do.utils import get_object, schedule_job


#-------------------------------------------------------------------------------
class UtilsTests(unittest.TestCase):

    #---------------------------------------------------------------------------
    def test_get_class(self):
        cl = get_object('scrapy_do.webservice.Status')
        self.assertEqual(cl.__name__, 'Status')

        with self.assertRaises(ModuleNotFoundError):
            get_object('foo.bar')

        with self.assertRaises(AttributeError):
            get_object('scrapy_do.bar')

    #---------------------------------------------------------------------------
    def test_schedule_job(self):
        scheduler = schedule.Scheduler()

        invalid_specs = ['', 'foo bar', 'every 2', 'every 2 foobar',
                         'every 2 to foo days', 'every monday at foo',
                         'every monday at foo:bar', 'every 2 day']
        valid_specs = ['every 2 days', 'every 3 to 5 days',
                       'every monday at 17:51']

        def mock_job():
            print('foo')

        for spec in invalid_specs:
            with self.assertRaises(ValueError):
                schedule_job(scheduler, spec).do(mock_job)

        for spec in valid_specs:
            schedule_job(scheduler, spec).do(mock_job)
