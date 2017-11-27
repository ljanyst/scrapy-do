#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   27.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import os

from twisted.application.service import MultiService
from scrapy_do.config import Config
from twisted.trial import unittest
from scrapy_do.app import ScrapyDoServiceMaker
from .utils import web_retrieve_async


#-------------------------------------------------------------------------------
class AppConfigTests(unittest.TestCase):

    #---------------------------------------------------------------------------
    def setUp(self):
        current_path = os.path.dirname(__file__)
        self.key_file = os.path.join(current_path, 'scrapy-do.key')
        self.cert_file = os.path.join(current_path, 'scrapy-do.crt')
        self.config_path = os.path.join(current_path, 'scrapy-do.conf')
        self.service_maker = ScrapyDoServiceMaker()

    #---------------------------------------------------------------------------
    def test_web_server_config(self):
        #-----------------------------------------------------------------------
        # Correct HTTP config
        #-----------------------------------------------------------------------
        config = Config([self.config_path])
        web_config = self.service_maker._validate_web_config(config)
        self.assertEqual(len(web_config), 5)

        #-----------------------------------------------------------------------
        # Correct HTTPS config
        #-----------------------------------------------------------------------
        config = Config([self.config_path])
        config.conf['web']['https'] = 'on'
        config.conf['web']['key'] = self.key_file
        config.conf['web']['cert'] = self.cert_file
        web_config = self.service_maker._validate_web_config(config)
        self.assertEqual(len(web_config), 5)

        #-----------------------------------------------------------------------
        # Incorrect HTTP config
        #-----------------------------------------------------------------------
        config = Config([self.config_path])
        config.conf['web']['port'] = 'asdf'
        self.assertRaises(ValueError,
                          f=self.service_maker._validate_web_config,
                          config=config)

        #-----------------------------------------------------------------------
        # Incorrect HTTPS config
        #-----------------------------------------------------------------------
        config = Config([self.config_path])
        config.conf['web']['https'] = 'on'
        config.conf['web']['key'] = self.key_file + 'foo'
        config.conf['web']['cert'] = self.cert_file
        self.assertRaises(FileNotFoundError,
                          f=self.service_maker._validate_web_config,
                          config=config)

    #---------------------------------------------------------------------------
    def test_web_server(self):
        #-----------------------------------------------------------------------
        # Correct HTTP config
        #-----------------------------------------------------------------------
        config = Config([self.config_path])
        self.service_maker._configure_web_server(config)

        #-----------------------------------------------------------------------
        # Correct HTTPS config
        #-----------------------------------------------------------------------
        config = Config([self.config_path])
        config.conf['web']['https'] = 'on'
        config.conf['web']['key'] = self.key_file
        config.conf['web']['cert'] = self.cert_file
        self.service_maker._configure_web_server(config)

    #---------------------------------------------------------------------------
    def test_service_maker(self):
        #-----------------------------------------------------------------------
        # Incorrect HTTP config
        #-----------------------------------------------------------------------
        config_path = os.path.join(os.path.dirname(__file__),
                                   'scrapy-do-broken-port.conf')
        self.config_path = config_path
        options = self.service_maker.options()
        options['config'] = config_path
        service = self.service_maker.makeService(options)
        self.assertIsInstance(service, MultiService)


#-------------------------------------------------------------------------------
class AppTests(unittest.TestCase):

    #---------------------------------------------------------------------------
    def setUp(self):
        service_maker = ScrapyDoServiceMaker()
        options = service_maker.options()
        config_path = os.path.join(os.path.dirname(__file__), 'scrapy-do.conf')
        self.config_path = config_path
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
