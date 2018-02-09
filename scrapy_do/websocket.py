#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   08.02.2018
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import socket
import psutil
import time
import json
import os

from autobahn.twisted.websocket import WebSocketServerProtocol
from autobahn.twisted.websocket import WebSocketServerFactory
from scrapy_do import __version__


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
        self.send_daemon_info()
        self.send_projects_info()
        self.send_jobs_info()

    #---------------------------------------------------------------------------
    def onMessage(self, payload, isBinary):
        pass

    #---------------------------------------------------------------------------
    def onClose(self, wasClean, code, reason):
        pass

    #---------------------------------------------------------------------------
    def send_json(self, msg):
        data = json.dumps(msg) + '\n'
        data = data.encode('utf-8')
        self.sendMessage(data)

    #---------------------------------------------------------------------------
    def send_daemon_info(self):
        p = psutil.Process(os.getpid())
        msg = {
            'type': 'DAEMON_INFO',
            'memoryUsage': float(p.memory_info().rss) / 1024. / 1024.,
            'cpuUsage': p.cpu_percent(),
            'time': int(time.time()),
            'timezone': "{}; {}".format(time.tzname[0], time.tzname[1]),
            'hostname': socket.gethostname(),
            'startTime': int(self.controller.start_time.timestamp()),
            'daemonVersion': __version__,
        }
        self.send_json(msg)

    #---------------------------------------------------------------------------
    def send_projects_info(self):
        controller = self.controller
        all_spiders = \
            [spider for prj in controller.projects for spider in prj.spiders]

        msg = {
            'type': 'PROJECTS_INFO',
            'projects': len(controller.projects),
            'spiders': len(all_spiders),
        }
        self.send_json(msg)

    #---------------------------------------------------------------------------
    def send_jobs_info(self):
        msg = {
            'type': 'JOBS_INFO',
            'jobsRun': self.controller.counter_run,
            'jobsSuccessful': self.controller.counter_success,
            'jobsFailed': self.controller.counter_failure,
            'jobsCanceled': self.controller.counter_cancel,
            'jobsScheduled': len(self.controller.scheduled_jobs),
        }
        self.send_json(msg)
