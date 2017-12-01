#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   27.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import unittest
import json

from scrapy_do.webservice import Status
from unittest.mock import Mock


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
