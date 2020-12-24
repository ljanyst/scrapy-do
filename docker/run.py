#!/usr/bin/env python
#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   26.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

from twisted.scripts.twistd import _SomeApplicationRunner, ServerOptions
from twisted.application import app
from scrapy_do.app import ScrapyDoServiceMaker


class ScrapyDoRunnerOptions(ServerOptions):
    @property
    def subCommands(self):
        sm = ScrapyDoServiceMaker()
        self.loadedPlugins = {sm.tapname: sm}
        yield (sm.tapname, None, sm.options, sm.description)

def run_app(config):
    _SomeApplicationRunner(config).run()


app.run(run_app, ScrapyDoRunnerOptions)