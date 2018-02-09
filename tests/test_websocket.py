#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   08.02.2018
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import unittest

from scrapy_do.websocket import WSFactory, WSProtocol
from unittest.mock import Mock, patch


#-------------------------------------------------------------------------------
class WebSocketTests(unittest.TestCase):

    #---------------------------------------------------------------------------
    def test_server_status(self):
        controller = Mock()
        controller.counter_run = 0
        controller.start_time.timestamp.return_value = 0
        controller.projects = []
        controller.scheduled_jobs = []
        controller.counter_cancel = 0
        controller.counter_failure = 0
        controller.counter_success = 0
        controller.counter_run = 0
        factory = WSFactory(controller=controller)
        factory.protocol = WSProtocol
        protocol = factory.buildProtocol(None)

        with patch.object(WSProtocol, "sendMessage"):
            protocol.onOpen()
            protocol.onMessage(None, None)
            protocol.onClose(None, None, None)
