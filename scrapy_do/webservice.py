#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   26.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

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
