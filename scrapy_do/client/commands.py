#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   24.01.2018
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import sys
import os

from scrapy_do.client.archive import build_project_archive
from scrapy_do.utils import exc_repr
from collections import namedtuple


#-------------------------------------------------------------------------------
Command = namedtuple('Command', [
    'arg_setup', 'arg_process', 'url_setup', 'response_parse', 'method'
])


#-------------------------------------------------------------------------------
def url_append(path):
    """
    Return a function computing an URL by appending the path to the appropriate
    argument
    """
    return lambda args: args.url + path


#-------------------------------------------------------------------------------
# Status
#-------------------------------------------------------------------------------
def status_arg_setup(subparsers):
    parser = subparsers.add_parser('status', help='Status of the service')
    parser.set_defaults(command='status')


def status_rsp_parse(rsp):
    data = []
    for k, v in rsp.items():
        data.append([k, v])
    headers = ['key', 'value']
    return {'headers': headers, 'data': data}


status_cmd = Command(
    status_arg_setup, lambda x: {}, url_append('/status.json'),
    status_rsp_parse, 'GET')


#-------------------------------------------------------------------------------
# List projects
#-------------------------------------------------------------------------------
def list_projects_arg_setup(subparsers):
    parser = subparsers.add_parser('list-projects', help='List the projects')
    parser.set_defaults(command='list-projects')


def list_projects_rsp_parse(rsp):
    data = []
    for project in rsp['projects']:
        data.append([project])
    headers = ['name']
    return {'headers': headers, 'data': data}


list_projects_cmd = Command(
    list_projects_arg_setup, lambda x: {}, url_append('/list-projects.json'),
    list_projects_rsp_parse, 'GET')


#-------------------------------------------------------------------------------
# List spiders
#-------------------------------------------------------------------------------
def list_spiders_arg_setup(subparsers):
    parser = subparsers.add_parser('list-spiders', help='List the spiders')
    parser.set_defaults(command='list-spiders')
    parser.add_argument('--project', type=str, default=None,
                        help='project name')


def list_spiders_arg_process(args):
    if args.project is None:
        print('[!] You need to specify the project name.')
        sys.exit(1)
    return {'project': args.project}


def list_spiders_rsp_parse(rsp):
    data = []
    for spider in rsp['spiders']:
        data.append([spider])
    headers = ['name']
    return {'headers': headers, 'data': data}


list_spiders_cmd = Command(
    list_spiders_arg_setup, list_spiders_arg_process,
    url_append('/list-spiders.json'), list_spiders_rsp_parse, 'GET')


#-------------------------------------------------------------------------------
# List jobs
#-------------------------------------------------------------------------------
def list_jobs_arg_setup(subparsers):
    parser = subparsers.add_parser('list-jobs', help='List the jobs')
    parser.set_defaults(command='list-jobs')
    parser.add_argument('--status', type=str, default='ACTIVE',
                        choices=['ACTIVE', 'COMPLETED', 'SCHEDULED', 'PENDING',
                                 'RUNNING', 'CANCELED', 'SUCCESSFUL', 'FAILED'],
                        help='job status of the jobs to list')
    parser.add_argument('--job-id', type=str, default=None,
                        help='ID of the job to list')


def list_jobs_arg_process(args):
    if args.job_id is not None:
        return {'id': args.job_id}
    return {'status': args.status}


def list_jobs_rsp_parse(rsp):
    data = []
    headers = ['identifier', 'project', 'spider', 'status', 'schedule', 'actor',
               'timestamp', 'duration']
    for job in rsp['jobs']:
        datum = []
        for h in headers:
            datum.append(job[h])
        data.append(datum)
    return {'headers': headers, 'data': data}


list_jobs_cmd = Command(
    list_jobs_arg_setup, list_jobs_arg_process, url_append('/list-jobs.json'),
    list_jobs_rsp_parse, 'GET')


#-------------------------------------------------------------------------------
# Get log
#-------------------------------------------------------------------------------
def get_log_arg_setup(subparsers):
    parser = subparsers.add_parser('get-log', help='Get log')
    parser.set_defaults(command='get-log')
    parser.add_argument('--job-id', type=str, default=None,
                        help='job ID')
    parser.add_argument('--log-type', type=str, default='err',
                        choices=['out', 'err'], help='log type')


def get_log_url_setup(args):
    if args.job_id is None:
        print('[!] You need to specify a job ID.')
        sys.exit(1)
    return '{}/get-log/data/{}.{}'.format(args.url, args.job_id, args.log_type)


get_log_cmd = Command(
    get_log_arg_setup, lambda x: {}, get_log_url_setup, lambda x: x,
    'GET')


#-------------------------------------------------------------------------------
# Push project
#-------------------------------------------------------------------------------
def push_project_arg_setup(subparsers):
    parser = subparsers.add_parser('push-project', help='Upload a project')
    parser.set_defaults(command='push-project')
    parser.add_argument('--project-path', type=str, default='.',
                        help='project path')


def push_project_arg_process(args):
    path = os.getcwd()
    if args.project_path.startswith('/'):
        path = args.project_path
    else:
        path = os.path.join(path, args.project_path)
        path = os.path.normpath(path)

    try:
        _, archive = build_project_archive(path)
        return {'archive': archive}
    except Exception as e:
        print('[!] Unable to create archive:', exc_repr(e))
        sys.exit(1)


def push_project_rsp_parse(rsp):
    data = []
    for spider in rsp['spiders']:
        data.append([spider])
    headers = [rsp['name']]
    return {'headers': headers, 'data': data}


push_project_cmd = Command(
    push_project_arg_setup, push_project_arg_process,
    url_append('/push-project.json'), push_project_rsp_parse, 'POST')


#-------------------------------------------------------------------------------
# Schedule job
#-------------------------------------------------------------------------------
def schedule_job_arg_setup(subparsers):
    parser = subparsers.add_parser('schedule-job', help='Schedule a job')
    parser.set_defaults(command='schedule-job')
    parser.add_argument('--project', type=str, default=None,
                        help='project name')
    parser.add_argument('--spider', type=str, default=None,
                        help='spider name')
    parser.add_argument('--when', type=str, default='now',
                        help='scheduling spec')


def schedule_job_arg_process(args):
    if args.project is None:
        print('[!] You need to specify the project name.')
        sys.exit(1)
    if args.spider is None:
        print('[!] You need to specify the spider name.')
        sys.exit(1)

    return {
        'project': args.project,
        'spider': args.spider,
        'when': args.when
    }


def schedule_job_rsp_parse(rsp):
    data = [[rsp['identifier']]]
    headers = ['identifier']
    return {'headers': headers, 'data': data}


schedule_job_cmd = Command(
    schedule_job_arg_setup, schedule_job_arg_process,
    url_append('/schedule-job.json'), schedule_job_rsp_parse, 'POST')


#-------------------------------------------------------------------------------
# Cancel job
#-------------------------------------------------------------------------------
def cancel_job_arg_setup(subparsers):
    parser = subparsers.add_parser('cancel-job', help='Cancel a job')
    parser.set_defaults(command='cancel-job')
    parser.add_argument('--job-id', type=str, default=None,
                        help='job ID')


def cancel_job_arg_process(args):
    if args.job_id is None:
        print('[!] You need to specify the job ID.')
        sys.exit(1)

    return {'id': args.job_id}


def cancel_job_rsp_parse(rsp):
    return 'Canceled.'


cancel_job_cmd = Command(
    cancel_job_arg_setup, cancel_job_arg_process,
    url_append('/cancel-job.json'), cancel_job_rsp_parse, 'POST')


#-------------------------------------------------------------------------------
# Remove project
#-------------------------------------------------------------------------------
def remove_project_arg_setup(subparsers):
    parser = subparsers.add_parser('remove-project', help='Remove a project')
    parser.set_defaults(command='remove-project')
    parser.add_argument('--name', type=str, default=None,
                        help='project name')


def remove_project_arg_process(args):
    if args.name is None:
        print('[!] You need to specify the project name.')
        sys.exit(1)
    return {'name': args.name}


def remove_project_rsp_parse(rsp):
    return 'Removed.'


remove_project_cmd = Command(
    remove_project_arg_setup, remove_project_arg_process,
    url_append('/remove-project.json'), remove_project_rsp_parse, 'POST')


#-------------------------------------------------------------------------------
# List of commands
#-------------------------------------------------------------------------------
commands = {
    'status': status_cmd,
    'list-projects': list_projects_cmd,
    'list-spiders': list_spiders_cmd,
    'list-jobs': list_jobs_cmd,
    'get-log': get_log_cmd,
    'push-project': push_project_cmd,
    'schedule-job': schedule_job_cmd,
    'cancel-job': cancel_job_cmd,
    'remove-project': remove_project_cmd
}
