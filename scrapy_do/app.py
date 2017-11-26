#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   26.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import os

from twisted.application.internet import TCPServer
from twisted.application.service import MultiService, IServiceMaker
from twisted.python import log, usage
from zope.interface import implementer
from twisted.web import server

from .config import Config
from .webservice import WebApp


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
    def makeService(self, options):
        top_service = MultiService()
        config_file = os.path.expanduser(options['config'])
        config = Config([config_file])

        #-----------------------------------------------------------------------
        # Set up the Web service
        #-----------------------------------------------------------------------
        interface = config.get_string('web', 'interface')
        port = config.get_int('web', 'port')
        webserver = TCPServer(port, server.Site(WebApp(config)),
                              interface=interface)
        webserver.setServiceParent(top_service)
        log.msg(format="Scrapy-Do web interface is available at "
                       "http://%(interface)s:%(port)s/",
                interface=interface, port=port)

        return top_service
