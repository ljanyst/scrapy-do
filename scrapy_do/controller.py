#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   03.12.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import tempfile
import pickle
import shutil
import os

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.utils import getProcessValue, getProcessOutputAndValue
from distutils.spawn import find_executable
from collections import namedtuple


#-------------------------------------------------------------------------------
Project = namedtuple('Project', ['name', 'archive', 'spiders'])


#-------------------------------------------------------------------------------
class Controller:
    """
    An object of this class is responsible for glueing together all the other
    components.
    """

    #---------------------------------------------------------------------------
    def __init__(self, config):
        self.config = config
        self.project_store = config.get_string('scrapy-do', 'project-store')
        self.metadata_path = os.path.join(self.project_store, 'metadata.pkl')

        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, 'rb') as f:
                self.projects = pickle.load(f)
        else:
            try:
                os.makedirs(self.project_store)
            except FileExistsError:
                pass
            self.projects = {}
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.projects, f)

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def push_project(self, name, data):
        #-----------------------------------------------------------------------
        # Store the data in a temoporary file
        #-----------------------------------------------------------------------
        tmp = tempfile.mkstemp()
        with open(tmp[0], 'wb') as f:
            f.write(data)

        #-----------------------------------------------------------------------
        # Unzip to a temporary directory
        #-----------------------------------------------------------------------
        temp_dir = tempfile.mkdtemp()

        unzip = find_executable('unzip')
        ret_code = yield getProcessValue(unzip, args=(tmp[1],), path=temp_dir)
        if ret_code != 0:
            shutil.rmtree(temp_dir)
            os.remove(tmp[1])
            raise ValueError('Not a valid zip archive')

        #-----------------------------------------------------------------------
        # Figure out the list of spiders
        #-----------------------------------------------------------------------
        temp_proj_dir = os.path.join(temp_dir, name)
        if not os.path.exists(temp_proj_dir):
            shutil.rmtree(temp_dir)
            os.remove(tmp[1])
            raise ValueError('Project {} not found in the archive'.format(name))

        scrapy = find_executable('scrapy')
        ret = yield getProcessOutputAndValue(scrapy, ('list',),
                                             path=temp_proj_dir)
        out, err, ret_code = ret

        if ret_code != 0:
            shutil.rmtree(temp_dir)
            os.remove(tmp[1])
            raise ValueError('Unable to get the list of spiders')

        spiders = out.decode('utf-8').split()

        shutil.rmtree(temp_dir)

        #-----------------------------------------------------------------------
        # Move to the final position and store the matadata
        #-----------------------------------------------------------------------
        archive = os.path.join(self.project_store, name + '.zip')
        shutil.move(tmp[1], archive)
        prj = Project(name, archive, spiders)
        self.projects[name] = prj
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.projects, f)

        returnValue(prj.spiders)
