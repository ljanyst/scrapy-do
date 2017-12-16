#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   27.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import tempfile
import shutil
import os

from twisted.application.service import MultiService
from twisted.internet.defer import inlineCallbacks
from scrapy_do.webservice import PublicHTMLRealm, get_web_app
from twisted.trial import unittest
from scrapy_do.app import ScrapyDoServiceMaker
from unittest.mock import Mock, patch
from .utils import web_retrieve_async
from copy import deepcopy


#-------------------------------------------------------------------------------
def build_mock_config(data):
    def get(section, option, default, dtype):
        try:
            val = data[section][option]
            if isinstance(val, dtype):
                return val
            if isinstance(val, Exception):
                raise val
            if dtype == str:
                return str(val)
            raise ValueError
        except (KeyError, ValueError):
            if default is not None:
                return default
            raise

    mock = Mock()
    mock.get_bool.side_effect = lambda s, o, d=None: get(s, o, d, bool)
    mock.get_int.side_effect = lambda s, o, d=None: get(s, o, d, int)
    mock.get_float.side_effect = lambda s, o, d=None: get(s, o, d, float)
    mock.get_string.side_effect = lambda s, o, d=None: get(s, o, d, str)
    mock.get_options.side_effect = lambda s: data[s].items()
    return mock


#-------------------------------------------------------------------------------
default_config = {
    'scrapy-do': {
        'project-store': 'projects',
        'job-slots': 2,
        'completed-cap': 3
    },
    'web': {
        'interfaces': '127.0.0.1:7654 [::1]:7654',
        'https': False,
        'auth': False,
        'cert': 'scrapy-do.crt',
        'key': 'scrapy-do.key',
        'chain': 'ca.crt'
    },
    'web-modules': {
        'status.json': 'scrapy_do.webservice.Status',
        'get-log': 'scrapy_do.webservice.GetLog'
    }
}


#-------------------------------------------------------------------------------
class AppConfigTests(unittest.TestCase):

    #---------------------------------------------------------------------------
    def setUp(self):
        current_path = os.path.dirname(__file__)
        cert_file = os.path.join(current_path, 'scrapy-do.crt')
        key_file = os.path.join(current_path, 'scrapy-do.key')
        chain_file = os.path.join(current_path, 'ca.crt')
        self.pstore_path = tempfile.mkdtemp()

        self.config = deepcopy(default_config)
        self.config['scrapy-do']['project-store'] = self.pstore_path
        self.config['web']['cert'] = cert_file
        self.config['web']['key'] = key_file
        self.config['web']['chain'] = chain_file

        self.service_maker = ScrapyDoServiceMaker()

    #---------------------------------------------------------------------------
    def test_web_server_config(self):
        #-----------------------------------------------------------------------
        # Correct HTTP config
        #-----------------------------------------------------------------------
        config = build_mock_config(self.config)
        web_config = self.service_maker._validate_web_config(config)
        self.assertEqual(len(web_config), 7)

        #-----------------------------------------------------------------------
        # Correct HTTPS config
        #-----------------------------------------------------------------------
        self.config['web']['https'] = True
        web_config = self.service_maker._validate_web_config(config)
        self.assertEqual(len(web_config), 7)
        self.config['web']['https'] = False

        #-----------------------------------------------------------------------
        # Incorrect HTTPS config
        #-----------------------------------------------------------------------
        self.config['web']['https'] = True
        self.config['web']['key'] += 'foo'
        self.assertRaises(FileNotFoundError,
                          f=self.service_maker._validate_web_config,
                          config=config)

    #---------------------------------------------------------------------------
    def test_web_server(self):
        #-----------------------------------------------------------------------
        # Correct HTTP config
        #-----------------------------------------------------------------------
        config = build_mock_config(self.config)
        controller = Mock()
        controller.log_dir = self.pstore_path
        self.service_maker._configure_web_server(config, controller)

        #-----------------------------------------------------------------------
        # Correct HTTPS config
        #-----------------------------------------------------------------------
        self.config['web']['https'] = True
        self.service_maker._configure_web_server(config, controller)

    #---------------------------------------------------------------------------
    def test_service_maker(self):
        #-----------------------------------------------------------------------
        # Incorrect HTTP config
        #-----------------------------------------------------------------------
        config_class = Mock()
        config = build_mock_config(self.config)
        config_class.return_value = config
        options = self.service_maker.options()
        with patch('scrapy_do.app.Config', config_class):
            self.config['web']['interfaces'] = ''
            service = self.service_maker.makeService(options)
            self.assertIsInstance(service, MultiService)
            self.config['web']['interfaces'] = 'localhost:7654'

        #-----------------------------------------------------------------------
        # Broken controller
        #-----------------------------------------------------------------------
        with patch('scrapy_do.app.Config', config_class):
            self.config['scrapy-do']['project-store'] = '/dev/null/foo'
            service = self.service_maker.makeService(options)
            self.assertIsInstance(service, MultiService)
            self.config['scrapy-do']['project-store'] = self.pstore_path

    #---------------------------------------------------------------------------
    def tearDown(self):
        shutil.rmtree(self.pstore_path)


#-------------------------------------------------------------------------------
class AppTestBase(unittest.TestCase):

    #---------------------------------------------------------------------------
    def set_up(self, auth):
        self.pstore_path = tempfile.mkdtemp()
        self.auth_file = tempfile.mkstemp()
        with open(self.auth_file[0], 'w') as f:
            print('foo:bar', file=f)

        self.config = deepcopy(default_config)
        self.config['scrapy-do']['project-store'] = self.pstore_path
        self.config['web']['auth-db'] = self.auth_file[1]
        self.config['web']['auth'] = auth

        service_maker = ScrapyDoServiceMaker()
        options = service_maker.options()

        config_class = Mock()
        config = build_mock_config(self.config)
        config_class.return_value = config
        with patch('scrapy_do.app.Config', config_class):
            self.service = service_maker.makeService(options)
        self.service.startService()

    #---------------------------------------------------------------------------
    def tear_down(self):
        shutil.rmtree(self.pstore_path)
        os.remove(self.auth_file[1])
        return self.service.stopService()


#-------------------------------------------------------------------------------
class AppNoAuthTest(AppTestBase):

    #---------------------------------------------------------------------------
    def setUp(self):
        self.set_up(False)

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def test_app(self):
        response = yield web_retrieve_async('GET', 'http://127.0.0.1:7654')
        resp = response[0]
        body = response[1]
        self.assertEqual(resp.code, 200)
        self.assertEqual(body.decode('utf-8'), '<html>Hello, world!</html>')

    #---------------------------------------------------------------------------
    def tearDown(self):
        return self.tear_down()


#-------------------------------------------------------------------------------
class AppAuthTest(AppTestBase):

    #---------------------------------------------------------------------------
    def setUp(self):
        self.set_up(True)

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def test_app(self):
        response = yield web_retrieve_async('GET', 'http://127.0.0.1:7654',
                                            username='foo', password='bar')
        resp = response[0]
        body = response[1]
        self.assertEqual(resp.code, 200)
        self.assertEqual(body.decode('utf-8'), '<html>Hello, world!</html>')

    #---------------------------------------------------------------------------
    def test_realm(self):
        config = Mock()
        controller = Mock()
        realm = PublicHTMLRealm(config, controller)
        self.assertRaises(NotImplementedError, realm.requestAvatar,
                          avatar_id='foo', mind='bar')

    #---------------------------------------------------------------------------
    def test_site(self):
        config = Mock()
        controller = Mock()
        get_web_app(config, controller)

    #---------------------------------------------------------------------------
    def tearDown(self):
        return self.tear_down()
