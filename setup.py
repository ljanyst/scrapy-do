#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   25.11.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import json
import sys
import os

from setuptools.command.build_py import build_py
from distutils.spawn import find_executable
from setuptools import setup
from subprocess import Popen
from scrapy_do import __version__
from shutil import copyfile, rmtree

#-------------------------------------------------------------------------------
# Package description
#-------------------------------------------------------------------------------
with open('README.rst') as readme:
    long_description = readme.read()


#-------------------------------------------------------------------------------
# Run command
#-------------------------------------------------------------------------------
def run_command(args, cwd):
    p = Popen(args, cwd=cwd)
    p.wait()
    return p.returncode


#-------------------------------------------------------------------------------
# Build the React web app
#-------------------------------------------------------------------------------
class build_ui(build_py):
    def run(self):
        if not self.dry_run:

            #-------------------------------------------------------------------
            # Check and set the environment up
            #-------------------------------------------------------------------
            target_dir = os.path.join(self.build_lib, 'scrapy_do', 'ui')

            if os.path.exists(target_dir):
                rmtree(target_dir)

            ui_path = os.path.join(os.getcwd(), 'ui')
            if not os.path.exists(ui_path):
                print('[!] The ui directory does not exist')
                sys.exit(1)

            npm = find_executable('npm')
            if npm is None:
                print('[!] You need to have node installed to build this app')
                sys.exit(1)

            #-------------------------------------------------------------------
            # Build the JavaScript code
            #-------------------------------------------------------------------
            ret = run_command([npm, 'install'], ui_path)
            if ret != 0:
                print('[!] Installation of JavaScript dependencies failed')
                sys.exit(1)

            ret = run_command([npm, 'run-script', 'build'], ui_path)
            if ret != 0:
                print('[!] Build of JavaScript artefacts failed')
                sys.exit(1)

            #-------------------------------------------------------------------
            # Create a list of artefacts
            #-------------------------------------------------------------------
            artefacts = [
                'asset-manifest.json',
                'favicon.png',
                'index.html',
                'manifest.json',
                'service-worker.js'
            ]

            build_dir = 'ui/build'
            asset_manifest = os.path.join(build_dir, artefacts[0])
            if not os.path.exists(asset_manifest):
                print('[!] Asset manifest does not exist.')
                sys.exit(1)

            assets = json.loads(open(asset_manifest, 'r').read())
            for _, asset in assets.items():
                artefacts.append(asset)

            #-------------------------------------------------------------------
            # Copy the artefacts to the dist root
            #-------------------------------------------------------------------
            print('Copying JavaScript artefacts to', target_dir)
            for artefact in artefacts:
                source_file = os.path.join(build_dir, artefact)
                target_file = os.path.join(target_dir, artefact)
                target_prefix = os.path.dirname(target_file)
                if not os.path.exists(target_prefix):
                    os.makedirs(target_prefix)
                copyfile(source_file, target_file)

        build_py.run(self)

#-------------------------------------------------------------------------------
# Setup
#-------------------------------------------------------------------------------
setup(
    name = 'scrapy-do',
    version = __version__,
    author = 'Lukasz Janyst',
    author_email = 'xyz@jany.st',
    url = 'https://jany.st/scrapy-do.html',
    description = 'A daemon for scheduling Scrapy spiders',
    long_description = long_description,
    license = 'BSD License',
    packages = ['scrapy_do', 'scrapy_do.client'],
    include_package_data = True,
    cmdclass={
        'build_py': build_ui
    },
    package_data={
        '': ['*.conf'],
    },
    scripts=['scrapy-do', 'scrapy-do-cl'],
    classifiers = [
        'Framework :: Scrapy',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Environment :: Console',
        'Environment :: No Input/Output (Daemon)',
    ],
    install_requires = [
        'scrapy', 'twisted', 'pyOpenSSL', 'psutil', 'python-dateutil',
        'schedule', 'pem', 'tabulate', 'requests', 'autobahn', 'tzlocal'
    ]
)
