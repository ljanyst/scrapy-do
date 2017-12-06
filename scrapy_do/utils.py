#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   26.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import importlib

from datetime import datetime


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


#-------------------------------------------------------------------------------
class TimeStamper:
    """
    Set the timestamp attribute of the object whenever the associated attribute
    is set. For example:

    :Example:

        >>> class Test:
        >>>     attr = TimeStamper('_attr')
        >>>
        >>>     def __init__(self, attr):
        >>>         self._attr = attr
        >>>         self.timestamp = datetime.now()
        >>> test = Test('foo')
        >>> test.attr
        'foo'
        >>> test.timestamp
        datetime.datetime(2017, 12, 2, 23, 0, 56, 671634)
        >>> test.attr = 'bar'
        >>> test.timestamp
        datetime.datetime(2017, 12, 2, 23, 1, 9, 688899)
    """

    #---------------------------------------------------------------------------
    def __init__(self, attr_name):
        self.attr_name = attr_name

    #---------------------------------------------------------------------------
    def __get__(self, obj, obj_type):
        return getattr(obj, self.attr_name)

    #---------------------------------------------------------------------------
    def __set__(self, obj, value):
        obj.timestamp = datetime.now()
        return setattr(obj, self.attr_name, value)


#-------------------------------------------------------------------------------
def check_scheduling_spec(spec):
    pass


#-------------------------------------------------------------------------------
def arg_require_all(dict, args):
    for arg in args:
        if arg not in dict:
            raise KeyError('Missing argument "{}"'.format(arg))


#-------------------------------------------------------------------------------
def arg_require_any(dict, args):
    for arg in args:
        if arg in dict:
            return
    raise KeyError('Neither argument present: "{}"'.format(str(args)))
