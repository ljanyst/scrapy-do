#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   27.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import os

from twisted.trial import unittest
from scrapy_do.app import ScrapyDoServiceMaker
from .utils import web_retrieve_async


#-------------------------------------------------------------------------------
class AppTests(unittest.TestCase):

    #---------------------------------------------------------------------------
    def setUp(self):
        service_maker = ScrapyDoServiceMaker()
        options = service_maker.options()
        config_path = os.path.join(os.path.dirname(__file__), 'scrapy-do.conf')
        options['config'] = config_path
        self.service = service_maker.makeService(options)
        self.service.startService()

    #---------------------------------------------------------------------------
    def test_app(self):
        def test_body(body):
            self.failUnlessEqual(body.decode('utf-8'),
                                 '<html>Hello, world!</html>')

        d = web_retrieve_async('GET', 'http://127.0.0.1:7654',
                               body_callback=test_body)
        return d

    #---------------------------------------------------------------------------
    def tearDown(self):
        return self.service.stopService()
