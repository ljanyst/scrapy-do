#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   16.12.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import configparser
import unittest
import argparse
import tempfile
import zipfile
import shutil
import os

from scrapy_do.client.archive import build_project_archive
from scrapy_do.client.webclient import request
from unittest.mock import Mock, patch, DEFAULT

import scrapy_do.client.commands as cmd


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

    #---------------------------------------------------------------------------
    def test_web_client(self):
        with patch.multiple('requests', post=DEFAULT, get=DEFAULT) as mock:
            #-------------------------------------------------------------------
            # Correct and successful POST request
            #-------------------------------------------------------------------
            response = Mock()
            response.status_code = 200
            response.headers = {'Content-Type': 'application/json'}
            mock['post'].return_value = response
            request('POST', 'foo', ssl_verify=False)

            #-------------------------------------------------------------------
            # Incorrect GET request
            #-------------------------------------------------------------------
            mock['get'].side_effect = Exception('Request failed')
            with self.assertRaises(Exception):
                request('GET', 'foo')

            #-------------------------------------------------------------------
            # Correct but failed POST request
            #-------------------------------------------------------------------
            mock['post'].reset()
            response = Mock()
            response.status_code = 400
            response.headers = {'Content-Type': 'application/json'}
            response.json.side_effect = {'msg': 'foo'}
            mock['post'].return_value = response
            with self.assertRaises(Exception):
                request('POST', 'foo')

            #-------------------------------------------------------------------
            # Correct text POST
            #-------------------------------------------------------------------
            mock['post'].reset()
            response = Mock()
            response.status_code = 200
            response.text.side_effect = 'foo'
            response.headers = {'Content-Type': 'plain/text'}
            mock['post'].return_value = response
            request('POST', 'foo', auth=('test', 'test'))

            #-------------------------------------------------------------------
            # Correct but failed text POST
            #-------------------------------------------------------------------
            mock['post'].reset()
            response = Mock()
            response.status_code = 400
            response.text.side_effect = 'foo'
            response.headers = {'Content-Type': 'plain/text'}
            mock['post'].return_value = response
            with self.assertRaises(Exception):
                request('POST', 'foo')

    #---------------------------------------------------------------------------
    def test_url_setup(self):
        #-----------------------------------------------------------------------
        # URL append
        #-----------------------------------------------------------------------
        args = Mock()
        args.url = '/foo'
        append = cmd.url_append('/bar')
        result = append(args)
        self.assertEqual(result, '/foo/bar')

        #-----------------------------------------------------------------------
        # Get log
        #-----------------------------------------------------------------------
        args = Mock()
        args.url = '/foo'
        args.job_id = 'bar'
        args.log_type = 'out'
        result = cmd.get_log_url_setup(args)
        self.assertEqual(result, '/foo/get-log/data/bar.out')

        args.job_id = None
        with patch('sys.exit') as exit:
            with patch('builtins.print'):
                cmd.get_log_url_setup(args)
                exit.assert_called_once()

    #---------------------------------------------------------------------------
    def test_arg_setup(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(help='Commands')
        cmd.status_arg_setup(subparsers)
        cmd.list_projects_arg_setup(subparsers)
        cmd.list_spiders_arg_setup(subparsers)
        cmd.list_jobs_arg_setup(subparsers)
        cmd.get_log_arg_setup(subparsers)
        cmd.push_project_arg_setup(subparsers)
        cmd.schedule_job_arg_setup(subparsers)
        cmd.cancel_job_arg_setup(subparsers)

    #---------------------------------------------------------------------------
    def test_arg_process(self):
        #-----------------------------------------------------------------------
        # List spiders
        #-----------------------------------------------------------------------
        args = Mock()
        args.project = 'foo'
        payload = cmd.list_spiders_arg_process(args)
        self.assertIn('project', payload)
        self.assertEqual(payload['project'], 'foo')

        args.project = None
        with patch('sys.exit') as exit:
            with patch('builtins.print'):
                cmd.list_spiders_arg_process(args)
                exit.assert_called_once()

        #-----------------------------------------------------------------------
        # List jobs
        #-----------------------------------------------------------------------
        args = Mock()
        args.status = 'foo'
        args.job_id = None
        payload = cmd.list_jobs_arg_process(args)
        self.assertIn('status', payload)
        self.assertEqual(payload['status'], 'foo')
        args.job_id = 'foo'
        payload = cmd.list_jobs_arg_process(args)
        self.assertIn('id', payload)
        self.assertEqual(payload['id'], 'foo')

        #-----------------------------------------------------------------------
        # Push project
        #-----------------------------------------------------------------------
        args = Mock()
        args.project_path = '.'
        with patch('scrapy_do.client.commands.build_project_archive') as bpa:
            bpa.return_value = ('foo', 'bar')
            payload = cmd.push_project_arg_process(args)
        self.assertIn('name', payload)
        self.assertIn('archive', payload)
        self.assertEqual(payload['name'], 'foo')
        self.assertEqual(payload['archive'], 'bar')
        args.project_path = '/'
        with patch('scrapy_do.client.commands.build_project_archive') as bpa:
            bpa.return_value = ('foo', 'bar')
            payload = cmd.push_project_arg_process(args)

        #-----------------------------------------------------------------------
        # Schedule job
        #-----------------------------------------------------------------------
        args = Mock()
        args.project = 'foo'
        args.spider = 'bar'
        args.when = 'now'
        payload = cmd.schedule_job_arg_process(args)
        self.assertIn('project', payload)
        self.assertIn('spider', payload)
        self.assertIn('when', payload)
        self.assertEqual(payload['project'], 'foo')
        self.assertEqual(payload['spider'], 'bar')
        self.assertEqual(payload['when'], 'now')

        args.project = None
        with patch('sys.exit') as exit:
            with patch('builtins.print'):
                cmd.schedule_job_arg_process(args)
                exit.assert_called_once()

        args.project = 'foo'
        args.spider = None
        with patch('sys.exit') as exit:
            with patch('builtins.print'):
                cmd.schedule_job_arg_process(args)
                exit.assert_called_once()

        #-----------------------------------------------------------------------
        # Cancel Job
        #-----------------------------------------------------------------------
        args = Mock()
        args.job_id = 'foo'
        payload = cmd.cancel_job_arg_process(args)
        self.assertIn('id', payload)
        self.assertEqual(payload['id'], 'foo')

        args.job_id = None
        with patch('sys.exit') as exit:
            with patch('builtins.print'):
                cmd.cancel_job_arg_process(args)
                exit.assert_called_once()

    #---------------------------------------------------------------------------
    def test_rsp_parse(self):
        #-----------------------------------------------------------------------
        # Status
        #-----------------------------------------------------------------------
        rsp = {'foo1': 'bar1', 'foo2': 'bar2'}
        ret = cmd.status_rsp_parse(rsp)
        self.assertIn('key', ret['headers'])
        self.assertIn('value', ret['headers'])
        self.assertIn(['foo1', 'bar1'], ret['data'])
        self.assertIn(['foo2', 'bar2'], ret['data'])

        #-----------------------------------------------------------------------
        # List projects
        #-----------------------------------------------------------------------
        rsp = {'projects': ['prj1', 'prj2']}
        ret = cmd.list_projects_rsp_parse(rsp)
        self.assertIn('name', ret['headers'])
        self.assertIn(['prj1'], ret['data'])
        self.assertIn(['prj2'], ret['data'])

        #-----------------------------------------------------------------------
        # List spiders
        #-----------------------------------------------------------------------
        rsp = {'spiders': ['spider1', 'spider2']}
        ret = cmd.list_spiders_rsp_parse(rsp)
        self.assertIn('name', ret['headers'])
        self.assertIn(['spider1'], ret['data'])
        self.assertIn(['spider2'], ret['data'])

        #-----------------------------------------------------------------------
        # List jobs
        #-----------------------------------------------------------------------
        rsp = {'jobs': [{
            'identifier': 'foo',
            'project': 'foo',
            'spider': 'foo',
            'status': 'foo',
            'schedule': 'foo',
            'actor': 'foo',
            'timestamp': 'foo',
            'duration': 'foo'
        }]}
        ret = cmd.list_jobs_rsp_parse(rsp)
        self.assertIn(['foo'] * 8, ret['data'])

        #-----------------------------------------------------------------------
        # Push project
        #-----------------------------------------------------------------------
        rsp = {'spiders': ['spider1', 'spider2']}
        ret = cmd.push_project_rsp_parse(rsp)
        self.assertIn('spiders', ret['headers'])
        self.assertIn(['spider1'], ret['data'])
        self.assertIn(['spider2'], ret['data'])

        #-----------------------------------------------------------------------
        # Schedule job
        #-----------------------------------------------------------------------
        rsp = {'identifier': 'foo'}
        ret = cmd.schedule_job_rsp_parse(rsp)
        self.assertIn('identifier', ret['headers'])
        self.assertIn(['foo'], ret['data'])

        #-----------------------------------------------------------------------
        # Cancel job
        #-----------------------------------------------------------------------
        ret = cmd.cancel_job_rsp_parse(rsp)
        self.assertEqual(ret, 'Canceled.')
