#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   08.02.2018
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import unittest

from scrapy_do.websocket import WSFactory, WSProtocol
from unittest.mock import Mock


#-------------------------------------------------------------------------------
class WebSocketTests(unittest.TestCase):

    #---------------------------------------------------------------------------
    def test_creation(self):
        controller = Mock()
        factory = WSFactory(controller=controller)
        factory.protocol = WSProtocol
        protocol = factory.buildProtocol(None)
        protocol.onOpen()
        protocol.onMessage(None, None)
        protocol.onClose(None, None, None)
