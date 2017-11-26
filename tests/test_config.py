#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   25.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import unittest
import tempfile
import os

from configparser import NoSectionError, NoOptionError
from scrapy_do.config import Config

CONFIG_DATA = """
[tests]
bool2 = off
int2 = 43
string2 = bar
float2 = 4.3
"""


#-------------------------------------------------------------------------------
class ConfigTests(unittest.TestCase):
    #---------------------------------------------------------------------------
    def setUp(self):
        tmp = tempfile.mkstemp(text=True)
        self.config_file_name = tmp[1]
        with open(tmp[0], 'w') as f:
            f.write(CONFIG_DATA)

        self.config = Config(self.config_file_name, __package__)

    #---------------------------------------------------------------------------
    def test_config(self):
        with self.assertRaises(NoSectionError):
            self.config.get_int('foo', 'bar')

        with self.assertRaises(NoOptionError):
            self.config.get_int('tests', 'bar')

        with self.assertRaises(ValueError):
            self.config.get_int('tests', 'bool1')

        self.assertEqual(self.config.get_bool('tests', 'bool1'), True)
        self.assertEqual(self.config.get_bool('tests', 'bool2'), False)
        self.assertEqual(self.config.get_int('tests', 'int1'), 42)
        self.assertEqual(self.config.get_int('tests', 'int2'), 43)
        self.assertEqual(self.config.get_float('tests', 'float1'), 4.2)
        self.assertEqual(self.config.get_float('tests', 'float2'), 4.3)
        self.assertEqual(self.config.get_string('tests', 'string1'), 'foo')
        self.assertEqual(self.config.get_string('tests', 'string2'), 'bar')
        self.assertEqual(self.config.get_int('tests', 'string2', 42), 42)

    #---------------------------------------------------------------------------
    def tearDown(self):
        os.remove(self.config_file_name)
