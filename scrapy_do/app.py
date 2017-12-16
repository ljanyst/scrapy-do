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
from twisted.python import log, usage
from zope.interface import implementer
from twisted.web import server

from .webservice import get_web_app
from .controller import Controller
from .config import Config
from .utils import exc_repr, SSLCertOptions, decode_addresses


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
        interfaces = config.get_string('web', 'interfaces')
        interfaces = decode_addresses(interfaces)
        https = config.get_bool('web', 'https')
        auth = config.get_bool('web', 'auth')
        key_file = None
        cert_file = None
        chain_file = None
        auth_file = None
        files_to_check = []

        if not interfaces:
            raise ValueError('No valid web interfaces were configured')

        if https:
            key_file = config.get_string('web', 'key')
            cert_file = config.get_string('web', 'cert')
            chain_file = config.get_string('web', 'chain')
            files_to_check += [key_file, cert_file]
            if chain_file != '':
                files_to_check.append(chain_file)

        if auth:
            auth_file = config.get_string('web', 'auth-db')
            files_to_check.append(auth_file)

        for path in files_to_check:
            if not os.path.exists(path):
                raise FileNotFoundError(
                    "No such file or directory: '{}'".format(path))

        return interfaces, https, key_file, cert_file, chain_file, auth, \
            auth_file

    #---------------------------------------------------------------------------
    def _configure_web_server(self, config, controller):
        interfaces, https, key_file, cert_file, chain_file, _, _ = \
            self._validate_web_config(config)

        site = server.Site(get_web_app(config, controller))
        web_servers = []

        for interface, port in interfaces:
            if https:
                cf = SSLCertOptions(key_file, cert_file, chain_file)
                web_server = SSLServer(port, site, cf, interface=interface)
                method = 'https'
            else:
                web_server = TCPServer(port, site, interface=interface)
                method = 'http'

            web_servers.append(web_server)

            if ':' in interface:
                interface = '[{}]'.format(interface)
            log.msg(format="Scrapy-Do web interface is available at "
                           "%(method)s://%(interface)s:%(port)s/",
                    method=method, interface=interface, port=port)

        return web_servers

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
            web_servers = self._configure_web_server(config, controller)
            for web_server in web_servers:
                web_server.setServiceParent(top_service)
        except Exception as e:
            log.msg(format="Scrapy-Do web interface could not have been "
                           "configured: %(reason)s",
                    reason=exc_repr(e), logLevel=logging.ERROR)
            return top_service

        return top_service
