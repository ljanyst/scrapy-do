#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   16.12.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import configparser
import unittest
import tempfile
import zipfile
import shutil
import os

from scrapy_do.client.archive import build_project_archive


#-------------------------------------------------------------------------------
class ClientTests(unittest.TestCase):

    #---------------------------------------------------------------------------
    def test_archive_builder(self):
        #-----------------------------------------------------------------------
        # Create some real and hake projects
        #-----------------------------------------------------------------------
        temp_dir = tempfile.mkdtemp()

        zip_ref = zipfile.ZipFile('tests/quotesbot.zip', 'r')
        zip_ref.extractall(temp_dir)
        zip_ref.close()
        project_path = os.path.join(temp_dir, 'quotesbot')

        no_section_path = os.path.join(temp_dir, 'no-section')
        no_option_path = os.path.join(temp_dir, 'no-option')
        os.mkdir(no_section_path)
        os.mkdir(no_option_path)
        no_section_cfg = os.path.join(no_section_path, 'scrapy.cfg')
        no_option_cfg = os.path.join(no_option_path, 'scrapy.cfg')

        with open(no_section_cfg, 'w'):
            pass

        with open(no_option_cfg, 'w') as f:
            f.write('[deploy]\n')

        #-----------------------------------------------------------------------
        # Create the data archive
        #-----------------------------------------------------------------------
        with self.assertRaises(FileNotFoundError):
            build_project_archive(temp_dir)

        with self.assertRaises(configparser.NoSectionError):
            build_project_archive(no_section_path)

        with self.assertRaises(configparser.NoOptionError):
            build_project_archive(no_option_path)

        name, data = build_project_archive(project_path)

        #-----------------------------------------------------------------------
        # Clean up
        #-----------------------------------------------------------------------
        shutil.rmtree(temp_dir)
