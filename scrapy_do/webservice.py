#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   26.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import json

from twisted.cred.checkers import FilePasswordDB
from twisted.web.resource import IResource
from twisted.cred.portal import IRealm, Portal
from twisted.web.guard import HTTPAuthSessionWrapper, DigestCredentialFactory
from zope.interface import implementer
from twisted.web import resource


#-------------------------------------------------------------------------------
class WebApp(resource.Resource):

    isLeaf = True

    #---------------------------------------------------------------------------
    def __init__(self, config):
        super(WebApp, self).__init__()

    #---------------------------------------------------------------------------
    def render_GET(self, request):
        return "<html>Hello, world!</html>".encode('utf-8')


#-------------------------------------------------------------------------------
class JsonResource(resource.Resource):

    isLeaf = True

    #---------------------------------------------------------------------------
    def render(self, request):
        data = super(JsonResource, self).render(request)
        encoder = json.JSONEncoder()
        encoded = encoder.encode(data) + '\n'
        request.setHeader('Content-Type', 'application/json')
        request.setHeader('Content-Length', len(encoded))
        return encoded.encode('utf-8')


#-------------------------------------------------------------------------------
@implementer(IRealm)
class PublicHTMLRealm:

    #---------------------------------------------------------------------------
    def __init__(self, config):
        super(PublicHTMLRealm, self).__init__()
        self.config = config

    #---------------------------------------------------------------------------
    def requestAvatar(self, avatar_id, mind, *interfaces):
        if IResource in interfaces:
            return (IResource, WebApp(self.config), lambda: None)
        raise NotImplementedError()


#-------------------------------------------------------------------------------
def get_web_app(config):
    auth = config.get_bool('web', 'auth', False)
    if auth:
        auth_file = config.get_string('web', 'auth-db')
        portal = Portal(PublicHTMLRealm(config),
                        [FilePasswordDB(auth_file)])
        credential_factory = DigestCredentialFactory('md5', b'scrapy-do')
        resource = HTTPAuthSessionWrapper(portal, [credential_factory])
        return resource

    return WebApp(config)
