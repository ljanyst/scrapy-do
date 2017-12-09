#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   03.12.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import tempfile
import logging
import pickle
import shutil
import os

from twisted.application.service import Service
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.utils import getProcessValue, getProcessOutputAndValue
from twisted.internet.task import LoopingCall
from distutils.spawn import find_executable
from twisted.python import log
from collections import namedtuple
from .schedule import Schedule, Job, Actor, Status
from schedule import Scheduler
from .utils import schedule_job, run_process, twisted_sleep, exc_repr


#-------------------------------------------------------------------------------
Project = namedtuple('Project', ['name', 'archive', 'spiders'])


#-------------------------------------------------------------------------------
class Controller(Service):
    """
    An object of this class is responsible for glueing together all the other
    components.
    """

    #---------------------------------------------------------------------------
    def __init__(self, config):
        #-----------------------------------------------------------------------
        # Configuration
        #-----------------------------------------------------------------------
        self.config = config
        self.project_store = config.get_string('scrapy-do', 'project-store')
        self.job_slots = config.get_int('scrapy-do', 'job-slots')
        self.metadata_path = os.path.join(self.project_store, 'metadata.pkl')
        self.schedule_path = os.path.join(self.project_store, 'schedule.db')
        self.log_dir = os.path.join(self.project_store, 'log-dir')
        self.spider_data_dir = os.path.join(self.project_store, 'spider-data')
        self.running_jobs = {}
        self.scheduled_jobs = {}

        #-----------------------------------------------------------------------
        # Create all the directories
        #-----------------------------------------------------------------------
        dirs = [self.project_store, self.log_dir, self.spider_data_dir]
        for d in dirs:
            try:
                os.makedirs(d)
            except FileExistsError:
                pass

        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, 'rb') as f:
                self.projects = pickle.load(f)
        else:
            self.projects = {}
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.projects, f)

        #-----------------------------------------------------------------------
        # Set the scheduler up
        #-----------------------------------------------------------------------
        self.schedule = Schedule(self.schedule_path)
        self.scheduler = Scheduler()

        for job in self.schedule.get_jobs(Status.SCHEDULED):
            sch_job = schedule_job(self.scheduler, job.schedule)
            sch_job.do(lambda: self.schedule_job(job.project, job.spider, 'now',
                                                 Actor.SCHEDULER))
            self.scheduled_jobs[job.identifier] = sch_job

        #-----------------------------------------------------------------------
        # If we have any jobs marked as RUNNING in the schedule at this point,
        # it means that the daemon was killed while the jobs were running. We
        # mark these jobs as pending, so that they can be restarted as soon
        # as possible
        #-----------------------------------------------------------------------
        for job in self.schedule.get_jobs(Status.RUNNING):
            job.status = Status.PENDING
            self.schedule.commit_job(job)

        #-----------------------------------------------------------------------
        # Set up the service
        #-----------------------------------------------------------------------
        self.setName('Controller')
        self.scheduler_loop = LoopingCall(self.run_scheduler)
        self.crawlers_loop = LoopingCall(self.run_crawlers)

    #---------------------------------------------------------------------------
    def startService(self):
        self.scheduler_loop.start(1.)
        self.crawlers_loop.start(1.)

    #---------------------------------------------------------------------------
    def stopService(self):
        self.scheduler_loop.stop()
        self.crawlers_loop.stop()
        return self.wait_for_running_jobs(cancel=True)

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

    #---------------------------------------------------------------------------
    def get_projects(self):
        return list(self.projects.keys())

    #---------------------------------------------------------------------------
    def get_spiders(self, project_name):
        if project_name not in self.projects.keys():
            raise KeyError('Unknown project ' + project_name)
        return self.projects[project_name].spiders

    #---------------------------------------------------------------------------
    def schedule_job(self, project, spider, when, actor=Actor.USER):
        if project not in self.projects.keys():
            raise KeyError('Unknown project ' + project)

        if spider not in self.projects[project].spiders:
            raise KeyError('Unknown spider {}/{}'.format(project, spider))

        job = Job(Status.PENDING, actor, 'now', project, spider)
        if when != 'now':
            sch_job = schedule_job(self.scheduler, when)
            sch_job.do(lambda: self.schedule_job(project, spider, 'now',
                                                 Actor.SCHEDULER))
            self.scheduled_jobs[job.identifier] = sch_job
            job.status = Status.SCHEDULED
            job.schedule = when

        self.schedule.add_job(job)
        return job.identifier

    #---------------------------------------------------------------------------
    def get_jobs(self, job_status):
        return self.schedule.get_jobs(job_status)

    #---------------------------------------------------------------------------
    def get_job(self, job_id):
        return self.schedule.get_job(job_id)

    #---------------------------------------------------------------------------
    def run_scheduler(self):
        self.scheduler.run_pending()

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def _run_crawler(self, project, spider, job_id):
        #-----------------------------------------------------------------------
        # Unzip to a temporary directory
        #-----------------------------------------------------------------------
        temp_dir = tempfile.mkdtemp()
        archive = os.path.join(self.project_store, project + '.zip')

        unzip = find_executable('unzip')
        ret_code = yield getProcessValue(unzip, args=(archive,), path=temp_dir)
        if ret_code != 0:
            shutil.rmtree(temp_dir)
            raise IOError('Cannot unzip the project archive')

        #-----------------------------------------------------------------------
        # Run the crawler
        #-----------------------------------------------------------------------
        temp_proj_dir = os.path.join(temp_dir, project)
        env = {'SPIDER_DATA_DIR': self.spider_data_dir}
        process, finished = run_process('scrapy', ['crawl', spider], job_id,
                                        self.log_dir, env=env,
                                        path=temp_proj_dir)

        #-----------------------------------------------------------------------
        # Clean up
        #-----------------------------------------------------------------------
        def clean_up(status):
            shutil.rmtree(temp_dir)
            return status
        finished.addBoth(clean_up)

        returnValue((process, finished))

    #---------------------------------------------------------------------------
    def run_crawlers(self):
        jobs = self.schedule.get_jobs(Status.PENDING)
        jobs.reverse()
        while len(self.running_jobs) < self.job_slots and jobs:
            #-------------------------------------------------------------------
            # Run the job
            #-------------------------------------------------------------------
            job = jobs.pop()
            job.status = Status.RUNNING
            self.schedule.commit_job(job)
            # Use a placeholder until the process is actually started, so that
            # we do not exceed the quota due to races.
            self.running_jobs[job.identifier] = None

            d = self._run_crawler(job.project, job.spider, job.identifier)

            #-------------------------------------------------------------------
            # Error starting the job
            #-------------------------------------------------------------------
            def spawn_errback(error, job):
                job.status = Status.FAILED
                self.schedule.commit_job(job)
                log.msg(format="Unable to start job %(id)s: %(reason)s",
                        reason=exc_repr(error.value), id=job.identifier,
                        logLevel=logging.ERROR)
                del self.running_jobs[job.identifier]

            #-------------------------------------------------------------------
            # Job started successfully
            #-------------------------------------------------------------------
            def spawn_callback(value, job):
                # Put the process object and the finish deferred in the
                # dictionary
                self.running_jobs[job.identifier] = value
                log.msg(format="Job %(id)s started successfully",
                        id=job.identifier, logLevel=logging.INFO)

                #---------------------------------------------------------------
                # Finish things up
                #---------------------------------------------------------------
                def finished_callback(exit_code):
                    if exit_code == 0:
                        job.status = Status.SUCCESSFUL
                    else:
                        job.status = Status.FAILED

                    log.msg(format="Job %(id)s exited with code %(exit_code)s",
                            id=job.identifier, exit_code=exit_code,
                            logLevel=logging.INFO)

                    self.schedule.commit_job(job)
                    del self.running_jobs[job.identifier]
                    return exit_code

                value[1].addCallback(finished_callback)

            d.addCallbacks(spawn_callback, spawn_errback,
                           callbackArgs=(job,), errbackArgs=(job,))

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def wait_for_starting_jobs(self):
        num_starting = 1  # whatever to loop at least once
        while num_starting:
            num_starting = 0
            for k, v in self.running_jobs.items():
                if v is None:
                    num_starting += 1
            yield twisted_sleep(0.1)

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def wait_for_running_jobs(self, cancel=False):
        yield self.wait_for_starting_jobs()

        #-----------------------------------------------------------------------
        # Send SIGTERM if requested
        #-----------------------------------------------------------------------
        if cancel:
            for job_id in self.running_jobs:
                process, _ = self.running_jobs[job_id]
                process.signalProcess('TERM')

        #-----------------------------------------------------------------------
        # Wait for the jobs to finish
        #-----------------------------------------------------------------------
        to_finish = []
        for job_id in self.running_jobs:
            _, finished = self.running_jobs[job_id]
            to_finish.append(finished)

        for d in to_finish:
            yield d

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def cancel_job(self, job_id):
        job = self.schedule.get_job(job_id)

        #-----------------------------------------------------------------------
        # Scheduled
        #-----------------------------------------------------------------------
        if job.status == Status.SCHEDULED:
            job.status = Status.CANCELED
            self.schedule.commit_job(job)
            self.scheduler.cancel_job(self.scheduled_jobs[job_id])
            del self.scheduled_jobs[job_id]

        #-----------------------------------------------------------------------
        # Pending
        #-----------------------------------------------------------------------
        elif job.status == Status.PENDING:
            job.status = Status.CANCELED
            self.schedule.commit_job(job)

        #-----------------------------------------------------------------------
        # Running
        #-----------------------------------------------------------------------
        elif job.status == Status.RUNNING:
            while True:
                if job_id not in self.running_jobs:
                    raise KeyError('Job {} is not active'.format(job_id))
                if self.running_jobs[job_id] is None:
                    yield twisted_sleep(0.1)  # wait until the job starts
                else:
                    break
            process, finished = self.running_jobs[job_id]
            process.signalProcess('TERM')
            yield finished
            job.status = Status.CANCELED
            self.schedule.commit_job(job)

        #-----------------------------------------------------------------------
        # Not active
        #-----------------------------------------------------------------------
        else:
            raise KeyError('Job {} is not active'.format(job_id))
