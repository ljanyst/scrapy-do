#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   27.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import hashlib
import json

from twisted.internet.protocol import Protocol
from twisted.web.http_headers import Headers
from twisted.internet.defer import Deferred
from twisted.web.client import Agent
from twisted.internet import reactor
from urllib.parse import urlparse


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
def md5sum(data):
    m = hashlib.md5()
    m.update(data.encode('utf-8'))
    return m.hexdigest()


#-------------------------------------------------------------------------------
def build_digest_header(method, url, username, password, auth_info):
    parsed_url = urlparse(url)
    nonce_count = '1'.zfill(8)
    cnonce = '12345678'
    nonce = auth_info['nonce']
    realm = auth_info['realm']
    qop = auth_info['qop']
    ha1 = md5sum('{}:{}:{}'.format(username, realm, password))
    ha2 = md5sum('{}:{}'.format(method, parsed_url.path))
    response_str = '{}:{}:{}:'.format(ha1, nonce, nonce_count)
    response_str += '{}:{}:{}'.format(cnonce, qop, ha2)
    response = md5sum(response_str)
    header = 'digest '
    header += 'username="{}" '.format(username)
    header += 'realm="{}" '.format(realm)
    header += 'nonce="{}" '.format(nonce)
    header += 'uri="{}" '.format(parsed_url.path)
    header += 'cnonce="{}" '.format(cnonce)
    header += 'nc="{}" '.format(nonce_count)
    header += 'qop="{}" '.format(qop)
    header += 'response="{}" '.format(response)
    header += 'opaque="{}" '.format(auth_info['opaque'])
    header += 'algorithm="{}"'.format(auth_info['algorithm'])
    return header


#-------------------------------------------------------------------------------
def web_retrieve_async(method, url, headers=None, body_producer=None,
                       username=None, password=None):

    #---------------------------------------------------------------------------
    # Send the initial request
    #---------------------------------------------------------------------------
    agent = Agent(reactor)
    method_enc = method.encode('utf-8')
    url_enc = url.encode('utf-8')
    d = agent.request(method_enc, url_enc, headers, body_producer)

    finished = Deferred()
    auth_tried = [False]

    #---------------------------------------------------------------------------
    # Process an error
    #---------------------------------------------------------------------------
    def cb_error(response):
        finished.callback(response)

    #---------------------------------------------------------------------------
    # Process the response
    #---------------------------------------------------------------------------
    def cb_response(response):
        resp_headers = dict(response.headers.getAllRawHeaders())
        auth_info = None

        #-----------------------------------------------------------------------
        # Process the authentication info
        #-----------------------------------------------------------------------
        if b'WWW-Authenticate' in resp_headers:
            auth_info = resp_headers[b'WWW-Authenticate'][0]
            auth_info = auth_info.decode('utf-8')
            if auth_info.startswith('digest'):
                auth_info = auth_info[7:].split(', ')
                auth_info = map(lambda x: x.split('='), auth_info)
                auth_info = map(lambda x: (x[0], x[1][1:-1]), auth_info)
                auth_info = dict(auth_info)

        #-----------------------------------------------------------------------
        # Authenticate if necessary and possible
        #
        # Python's scoping rules are demented. You can't overwrite a variable
        # from the parent scope in a closure without getting
        # UnboundLocalError exceptions in totally unexpected places. It's fine
        # to write to arrays though.
        #-----------------------------------------------------------------------
        if response.code == 401 and auth_info and username and password \
           and not auth_tried[0]:
            auth_tried[0] = True
            if headers is None:
                new_headers = Headers()
            else:
                new_headers = headers
            digest_header = build_digest_header(method, url, username, password,
                                                auth_info)
            new_headers.addRawHeader('Authorization', digest_header)
            d = agent.request(method_enc, url_enc, new_headers, body_producer)
            d.addCallbacks(cb_response, cb_error)

        #-----------------------------------------------------------------------
        # Fetch the body
        #-----------------------------------------------------------------------
        else:
            response.deliverBody(BodyCapture(response, finished))

    d.addCallbacks(cb_response, cb_error)
    return finished


#-------------------------------------------------------------------------------
def json_encode(data):
    data = json.dumps(data)
    return data.encode('utf-8')


#-------------------------------------------------------------------------------
def make_deferred_func(d):
    def func(*args, **kwargs):
        d.callback(None)
    return func
