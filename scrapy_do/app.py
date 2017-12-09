#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   26.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import logging
import os

from twisted.application.internet import TCPServer, SSLServer
from twisted.application.service import MultiService, IServiceMaker
from twisted.internet.ssl import DefaultOpenSSLContextFactory
from twisted.python import log, usage
from zope.interface import implementer
from twisted.web import server

from .webservice import get_web_app
from .controller import Controller
from .config import Config
from .utils import exc_repr


#-------------------------------------------------------------------------------
class ScrapyDoOptions(usage.Options):
    optParameters = [
        ['config', 'c', '~/scrapy-do/config', 'A configuration file to load'],
    ]


#-------------------------------------------------------------------------------
@implementer(IServiceMaker)
class ScrapyDoServiceMaker():

    tapname = "scrapy-do"
    description = "A service running scrapy spiders."
    options = ScrapyDoOptions

    #---------------------------------------------------------------------------
    def _validate_web_config(self, config):
        interface = config.get_string('web', 'interface')
        port = config.get_int('web', 'port')
        https = config.get_bool('web', 'https')
        auth = config.get_bool('web', 'auth')
        key_file = None
        cert_file = None
        auth_file = None
        files_to_check = []

        if https:
            key_file = config.get_string('web', 'key')
            cert_file = config.get_string('web', 'cert')
            files_to_check += [key_file, cert_file]

        if auth:
            auth_file = config.get_string('web', 'auth-db')
            files_to_check.append(auth_file)

        for path in files_to_check:
            if not os.path.exists(path):
                raise FileNotFoundError(
                    "No such file or directory: '{}'".format(path))

        return interface, port, https, key_file, cert_file, auth, auth_file

    #---------------------------------------------------------------------------
    def _configure_web_server(self, config, controller):
        interface, port, https, key_file, cert_file, _, _ = \
            self._validate_web_config(config)

        site = server.Site(get_web_app(config, controller))
        if https:
            context = DefaultOpenSSLContextFactory(key_file, cert_file)
            web_server = SSLServer(port, site, context, interface=interface)
            method = 'https'
        else:
            web_server = TCPServer(port, site, interface=interface)
            method = 'http'

        log.msg(format="Scrapy-Do web interface is available at "
                       "%(method)s://%(interface)s:%(port)s/",
                method=method, interface=interface, port=port)

        return web_server

    #---------------------------------------------------------------------------
    def makeService(self, options):
        top_service = MultiService()
        config_file = os.path.expanduser(options['config'])
        config = Config([config_file])

        #-----------------------------------------------------------------------
        # Set up the controller
        #-----------------------------------------------------------------------
        try:
            controller = Controller(config)
            controller.setServiceParent(top_service)
        except Exception as e:
            log.msg(format="Unable to set up the controller: %(reason)s",
                    reason=exc_repr(e), logLevel=logging.ERROR)
            return top_service

        #-----------------------------------------------------------------------
        # Set up the web server
        #-----------------------------------------------------------------------
        try:
            web_server = self._configure_web_server(config, controller)
            web_server.setServiceParent(top_service)
        except Exception as e:
            log.msg(format="Scrapy-Do web interface could not have been "
                           "configured: %(reason)s",
                    reason=exc_repr(e), logLevel=logging.ERROR)
            return top_service

        return top_service
