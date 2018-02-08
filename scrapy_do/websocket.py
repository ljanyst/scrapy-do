#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   08.02.2018
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

from autobahn.twisted.websocket import WebSocketServerProtocol
from autobahn.twisted.websocket import WebSocketServerFactory


#-------------------------------------------------------------------------------
class WSFactory(WebSocketServerFactory):

    #---------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        self.controller = kwargs.pop('controller')
        super(WSFactory, self).__init__(*args, **kwargs)

    #---------------------------------------------------------------------------
    def buildProtocol(self, addr):
        protocol = super(WSFactory, self).buildProtocol(addr)
        protocol.controller = self.controller
        return protocol


#-------------------------------------------------------------------------------
class WSProtocol(WebSocketServerProtocol):

    #---------------------------------------------------------------------------
    def onOpen(self):
        pass

    #---------------------------------------------------------------------------
    def onMessage(self, payload, isBinary):
        pass

    #---------------------------------------------------------------------------
    def onClose(self, wasClean, code, reason):
        pass
