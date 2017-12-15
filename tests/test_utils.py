#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   30.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import unittest
import schedule
import os

from dateutil.relativedelta import relativedelta
from scrapy_do.utils import get_object, schedule_job, pprint_relativedelta
from scrapy_do.utils import SSLCertOptions, decode_addresses
from datetime import datetime


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

    #---------------------------------------------------------------------------
    def test_pprint(self):
        now = datetime.now()
        future = now + relativedelta(years=+1, months=+2, days=+3, hours=+4,
                                     minutes=+5, seconds=+6)
        diff = pprint_relativedelta(relativedelta(future, now))
        self.assertEqual(diff, '1y 2m 3d 4h 5m 6s')

    #---------------------------------------------------------------------------
    def test_ssl_context_factory(self):
        current_path = os.path.dirname(__file__)
        cert_file = os.path.join(current_path, 'scrapy-do.crt')
        key_file = os.path.join(current_path, 'scrapy-do.key')
        chain_file = os.path.join(current_path, 'ca.crt')

        fact1 = SSLCertOptions(key_file, cert_file)
        fact2 = SSLCertOptions(key_file, cert_file, chain_file)

        context_old1 = fact1.getContext()
        context_old2 = fact2.getContext()

        context_nc1 = fact1.getContext()
        context_nc2 = fact2.getContext()

        fact1.load_time = 0
        fact2.load_time = 0

        context_new1 = fact1.getContext()
        context_new2 = fact2.getContext()

        self.assertEqual(context_old1, context_nc1)
        self.assertEqual(context_old2, context_nc2)
        self.assertNotEqual(context_old1, context_new1)
        self.assertNotEqual(context_old2, context_new2)

    #---------------------------------------------------------------------------
    def test_decode_addresses(self):
        test_string = '123.124.123.123:123 32.32.32.32:32 [::1]:20  '
        test_string += '[2001:db8:122:344::192.0.2.33]:12'
        addrs_decoded = decode_addresses(test_string)
        addrs = [
            ('123.124.123.123', 123), ('32.32.32.32', 32),
            ('::1', 20), ('2001:db8:122:344::192.0.2.33', 12)
        ]
        for addr in addrs:
            self.assertIn(addr, addrs_decoded)
