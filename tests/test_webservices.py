#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   27.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import json

from twisted.internet.defer import Deferred, inlineCallbacks
from scrapy_do.webservice import Status, PushProject
from twisted.web.server import NOT_DONE_YET
from unittest.mock import Mock
from twisted.trial import unittest


#-------------------------------------------------------------------------------
class WebServicesTests(unittest.TestCase):

    #---------------------------------------------------------------------------
    def setUp(self):
        self.web_app = Mock()

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
