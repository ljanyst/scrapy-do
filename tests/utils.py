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
    def __init__(self, response, finished):
        self.body = bytes()
        self.response = response
        self.finished = finished

    #---------------------------------------------------------------------------
    def dataReceived(self, data):
        self.body += data

    #---------------------------------------------------------------------------
    def connectionLost(self, reason):
        self.finished.callback((self.response, self.body))


#-------------------------------------------------------------------------------
def web_retrieve_async(method, uri, headers=None, body_producer=None):
    agent = Agent(reactor)
    d = agent.request(method.encode('utf-8'), uri.encode('utf-8'),
                      headers, body_producer)

    finished = Deferred()

    #---------------------------------------------------------------------------
    def cb_response(response):
        response.deliverBody(BodyCapture(response, finished))

    d.addCallback(cb_response)
    return finished
