#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   27.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

from twisted.internet.protocol import Protocol
from twisted.internet.defer import Deferred
from twisted.web.client import Agent
from twisted.internet import reactor


#-------------------------------------------------------------------------------
class BodyCapture(Protocol):
    #---------------------------------------------------------------------------
    def __init__(self, finished, callback):
        self.body = bytes()
        self.callback = callback
        self.finished = finished

    #---------------------------------------------------------------------------
    def dataReceived(self, data):
        self.body += data

    #---------------------------------------------------------------------------
    def connectionLost(self, reason):
        self.callback(self.body)
        self.finished.callback(None)


#-------------------------------------------------------------------------------
def web_retrieve_async(method, uri, headers=None, producer=None,
                       header_callback=None, body_callback=None):
    agent = Agent(reactor)
    d = agent.request(method.encode('utf-8'), uri.encode('utf-8'),
                      headers, producer)

    def cb_response(response):
        finished = Deferred()
        if header_callback is not None:
            header_callback(response)

        if body_callback is not None:
            response.deliverBody(BodyCapture(finished, body_callback))
        return finished

    d.addCallback(cb_response)
    return d
