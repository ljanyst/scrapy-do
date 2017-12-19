#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   16.12.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import configparser
import tempfile
import zipfile
import os

from glob import glob


#-------------------------------------------------------------------------------
def build_project_archive(path):
    """
    Build a deployable archive from the project contained in the path.

    :param path:                         path to the project
    :raises FileNotFoundError:           if 'scrapy.cfg' file is not in the
                                         directory
    :raises configparser.NoOptionError:  if 'scrapy.cfg' does not define the
                                         name of the project in the ``[deploy]``
                                         section
    :raises configparser.NoSectionError: if 'scrapy.cfg' does not have the
                                         ``[deploy]`` section
    """
    #---------------------------------------------------------------------------
    # Check if the config dir exist and if it contains deployment data
    #---------------------------------------------------------------------------
    path = os.path.normpath(path)
    config_path = os.path.join(path, 'scrapy.cfg')
    if not os.path.exists(config_path):
        raise FileNotFoundError(config_path)

    config = configparser.ConfigParser()
    config.read(config_path)
    name = config.get('deploy', 'project')
    globs = '**/*.py'
    try:
        globs = config.get('deploy', 'glob')
    except (configparser.NoOptionError, configparser.NoSectionError):
        pass
    globs = globs.split()

    #---------------------------------------------------------------------------
    # Build a file list
    #---------------------------------------------------------------------------
    files = [config_path]
    for gl in globs:
        glob_pattern = os.path.join(path, gl)
        files += glob(glob_pattern, recursive=True)

    #---------------------------------------------------------------------------
    # Create the archive
    #---------------------------------------------------------------------------
    temp_file = tempfile.mkstemp()
    os.close(temp_file[0])
    lpath = len(path) if path.endswith('/') else len(path) + 1
    with zipfile.ZipFile(temp_file[1], 'w') as zip_file:
        for f in files:
            f = os.path.normpath(f)
            zip_file.write(f, os.path.join(name, f[lpath:]))

    #---------------------------------------------------------------------------
    # Read the archive
    #---------------------------------------------------------------------------
    with open(temp_file[1], 'rb') as f:
        data = f.read()
    os.remove(temp_file[1])
    return name, data
