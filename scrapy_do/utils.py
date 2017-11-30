#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   26.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import importlib


#-------------------------------------------------------------------------------
def exc_repr(e):
    """
    Return a string representation of an exception together with the excepion
    name.
    """
    return "{}: {}".format(type(e).__name__, str(e))


#-------------------------------------------------------------------------------
def get_object(name):
    """
    Retrieve an object from a module given its fully qualified name. For
    example: `get_object('scrapy_do.webservice.Status')`
    """
    name = name.split('.')
    object_name = name[-1]
    module = importlib.import_module('.'.join(name[:-1]))
    return getattr(module, object_name)
