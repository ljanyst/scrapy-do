#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   30.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import unittest

from scrapy_do.utils import get_object


#-------------------------------------------------------------------------------
class utilsTests(unittest.TestCase):

    #---------------------------------------------------------------------------
    def test_get_class(self):
        cl = get_object('scrapy_do.webservice.Status')
        self.assertEqual(cl.__name__, 'Status')

        with self.assertRaises(ModuleNotFoundError):
            get_object('foo.bar')

        with self.assertRaises(AttributeError):
            get_object('scrapy_do.bar')
