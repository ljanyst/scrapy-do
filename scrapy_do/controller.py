#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   03.12.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

"""
All the functionality running for running the jobs and keeping a proper record
of them.
"""

import configparser
import tempfile
import psutil
import pickle
import shutil
import time
import os

from twisted.application.service import Service
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.utils import getProcessValue, getProcessOutputAndValue
from twisted.internet.task import LoopingCall
from distutils.spawn import find_executable
from twisted.logger import Logger
from collections import namedtuple
from .schedule import Schedule, Job, Actor, Status
from schedule import Scheduler
from datetime import datetime
from .utils import schedule_job, run_process, twisted_sleep, exc_repr
from enum import Enum
from glob import glob


#-------------------------------------------------------------------------------
Project = namedtuple('Project', ['name', 'archive', 'spiders'])
RunningJob = namedtuple('RunningJob', ['process', 'finished_d', 'time_started'])


#-------------------------------------------------------------------------------
class Event(Enum):
    """
    Controller even type.
    """
    DAEMON_STATUS_CHANGE = 1,
    PROJECT_PUSH = 2,
    PROJECT_REMOVE = 3,
    JOB_UPDATE = 4,
    JOB_REMOVE = 5


#-------------------------------------------------------------------------------
class Controller(Service):
    """
    An object of this class is responsible for glueing together all the other
    components. It needs the following options in the `scrapy-do` section of
    the configuration:

      * `project-store` - a directory for all the data and metadata.
      * `job-slots` - number of jobs to run in parallel
      * `completed-cap` - number of completed jobs to keep while purging the old
        jobs

    :param config: A :class:`Config <scrapy_do.config.Config>`.
                   contains the following options in the `scrapy-do` section:
    """

    log = Logger()

    #---------------------------------------------------------------------------
    def __init__(self, config):
        #-----------------------------------------------------------------------
        # Configuration
        #-----------------------------------------------------------------------
        self.log.info('Creating controller')
        self.config = config
        ps = config.get_string('scrapy-do', 'project-store')
        ps_abs = os.path.join(os.getcwd(), ps)
        self.project_store = ps if ps.startswith('/') else ps_abs
        self.job_slots = config.get_int('scrapy-do', 'job-slots')
        self.completed_cap = config.get_int('scrapy-do', 'completed-cap')
        self.metadata_path = os.path.join(self.project_store, 'metadata.pkl')
        self.schedule_path = os.path.join(self.project_store, 'schedule.db')
        self.log_dir = os.path.join(self.project_store, 'log-dir')
        self.spider_data_dir = os.path.join(self.project_store, 'spider-data')
        self.running_jobs = {}
        self.scheduled_jobs = {}
        self.counter_run = 0
        self.counter_success = 0
        self.counter_failure = 0
        self.counter_cancel = 0
        self.start_time = datetime.now()
        self.listeners = set()
        self.mem_usage = None
        self.mem_usage_ts = None

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
            self.log.info('Re-scheduling: {}'.format(str(job)))
            sch_job = schedule_job(self.scheduler, job.schedule)
            sch_job.do(lambda job: self.schedule_job(job.project, job.spider,
                                                     'now', Actor.SCHEDULER),
                       job)
            self.scheduled_jobs[job.identifier] = sch_job

        #-----------------------------------------------------------------------
        # If we have any jobs marked as RUNNING in the schedule at this point,
        # it means that the daemon was killed while the jobs were running. We
        # mark these jobs as pending, so that they can be restarted as soon
        # as possible
        #-----------------------------------------------------------------------
        for job in self.schedule.get_jobs(Status.RUNNING):
            self.log.info('Restarting interrupted: {}'.format(str(job)))
            job.status = Status.PENDING
            self._update_job(job)

        #-----------------------------------------------------------------------
        # Set up the service
        #-----------------------------------------------------------------------
        self.setName('Controller')
        self.scheduler_loop = LoopingCall(self.run_scheduler)
        self.crawlers_loop = LoopingCall(self.run_crawlers)
        self.purger_loop = LoopingCall(self.purge_completed_jobs)
        self.event_loop = LoopingCall(self.dispatch_periodic_events)

    #---------------------------------------------------------------------------
    def startService(self):
        """
        Start the twisted related functionality.
        """
        self.log.info('Starting controller')
        self.scheduler_loop.start(1.)
        self.crawlers_loop.start(1.)
        self.purger_loop.start(10.)
        self.event_loop.start(1.)

    #---------------------------------------------------------------------------
    def stopService(self):
        """
        Stop the twisted related functionality.
        """
        self.log.info('Stopping controller')
        self.scheduler_loop.stop()
        self.crawlers_loop.stop()
        self.purger_loop.stop()
        self.event_loop.stop()
        return self.wait_for_running_jobs(cancel=True)

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def push_project(self, data):
        """
        Register a project of a given name with the zipped code passed in data.

        :param data: Binary blob with a zipped project code
        :return:     A deferred that gets called back with a `Project` object,
                     or a `ValueError` failure.
        """
        self.log.info('Pushing new project')

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
            self.log.debug('Failed to unzip data using "{}"'.format(unzip))
            raise ValueError('Not a valid zip archive')

        #-----------------------------------------------------------------------
        # Figure out the list of spiders
        #-----------------------------------------------------------------------
        config_files = glob(os.path.join(temp_dir, '**/scrapy.cfg'))

        if not config_files:
            shutil.rmtree(temp_dir)
            os.remove(tmp[1])
            raise ValueError('No project found in the archive')

        config = configparser.ConfigParser()
        config.read(config_files[0])
        try:
            name = config.get('deploy', 'project')
        except (configparser.NoOptionError, configparser.NoSectionError):
            shutil.rmtree(temp_dir)
            os.remove(tmp[1])
            raise ValueError('Can\'t extract project name from the config file')

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
        # Check if we have had the project registered before and if we
        # have some scheduled jobs for the spiders of this project that
        # are not present in the new archive
        #-----------------------------------------------------------------------
        if name in self.projects:
            sched_jobs = self.schedule.get_scheduled_jobs(name)
            sched_spiders = [job.spider for job in sched_jobs]
            for spider in sched_spiders:
                if spider not in spiders:
                    os.remove(tmp[1])
                    msg = 'Spider {} is going to be removed but has ' \
                          'scheduled jobs'
                    msg = msg.format(spider)
                    self.log.info('Failed to push project "{}": {}'.format(
                        name, msg))
                    raise ValueError(msg)

        #-----------------------------------------------------------------------
        # Move to the final position and store the matadata
        #-----------------------------------------------------------------------
        archive = os.path.join(self.project_store, name + '.zip')
        shutil.move(tmp[1], archive)
        prj = Project(name, archive, spiders)
        self.projects[name] = prj
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.projects, f)

        self.log.info('Added project "{}" with spiders {}'.format(
            name, prj.spiders))

        self.dispatch_event(Event.PROJECT_PUSH, prj)
        returnValue(prj)

    #---------------------------------------------------------------------------
    def get_projects(self):
        """
        Get the names of all the registred projects.
        """
        return list(self.projects.keys())

    #---------------------------------------------------------------------------
    def get_spiders(self, project_name):
        """
        Get names of all the spiders in the project.

        :param project_name: Name of the project
        :raises ValueError:    If the project name is not known
        """
        if project_name not in self.projects.keys():
            raise ValueError('Unknown project ' + project_name)
        return self.projects[project_name].spiders

    #---------------------------------------------------------------------------
    def schedule_job(self, project, spider, when, actor=Actor.USER):
        """
        Schedule a crawler job.

        :param project: Name of the project
        :param spider:  Name of the spider
        :param when:    A scheduling spec as handled by :meth:`schedule_job
                        <scrapy_do.utils.schedule_job>`
        :param actor:   :data:`Actor <scrapy_do.schedule.Actor>` triggering the
                        event
        :return:        A string identifier of a job
        """
        if project not in self.projects.keys():
            raise ValueError('Unknown project ' + project)

        if spider not in self.projects[project].spiders:
            raise ValueError('Unknown spider {}/{}'.format(project, spider))

        job = Job(Status.PENDING, actor, 'now', project, spider)
        if when != 'now':
            sch_job = schedule_job(self.scheduler, when)
            sch_job.do(lambda: self.schedule_job(project, spider, 'now',
                                                 Actor.SCHEDULER))
            self.scheduled_jobs[job.identifier] = sch_job
            job.status = Status.SCHEDULED
            job.schedule = when

        self.log.info('Scheduling: {}'.format(str(job)))
        self.schedule.add_job(job)
        self.dispatch_event(Event.JOB_UPDATE, job)
        return job.identifier

    #---------------------------------------------------------------------------
    def get_jobs(self, job_status):
        """
        See :meth:`Schedule.get_jobs <scrapy_do.schedule.Schedule.get_jobs>`.
        """
        return self.schedule.get_jobs(job_status)

    #---------------------------------------------------------------------------
    def get_active_jobs(self):
        """
        See :meth:`Schedule.get_active_jobs
        <scrapy_do.schedule.Schedule.get_active_jobs>`.
        """
        return self.schedule.get_active_jobs()

    #---------------------------------------------------------------------------
    def get_completed_jobs(self):
        """
        See :meth:`Schedule.get_completed_jobs
        <scrapy_do.schedule.Schedule.get_completed_jobs>`.
        """
        return self.schedule.get_completed_jobs()

    #---------------------------------------------------------------------------
    def get_job(self, job_id):
        """
        See :meth:`Schedule.get_job <scrapy_do.schedule.Schedule.get_job>`.
        """
        return self.schedule.get_job(job_id)

    #---------------------------------------------------------------------------
    def get_job_logs(self, job_id):
        """
        Get paths to job log files.

        :return: A tuple containing paths to out and error logs or `None` if
                 one or both don't exist
        """
        path = os.path.join(self.log_dir, job_id)
        logs = []
        for log in ['out', 'err']:
            log_path = '{}.{}'.format(path, log)
            if os.path.exists(log_path):
                logs.append(log_path)
            else:
                logs.append(None)
        return tuple(logs)

    #---------------------------------------------------------------------------
    def run_scheduler(self):
        """
        Run the `schedule.Scheduler` jobs.
        """
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
            msg = 'Unable to unzip with {}. Archive corrupted?'.format(unzip)
            self.log.error(msg)
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
        """
        Spawn as many crawler processe out of pending jobs as there is free
        job slots.
        """
        jobs = self.schedule.get_jobs(Status.PENDING)
        jobs.reverse()
        while len(self.running_jobs) < self.job_slots and jobs:
            self.counter_run += 1
            #-------------------------------------------------------------------
            # Run the job
            #-------------------------------------------------------------------
            job = jobs.pop()
            job.status = Status.RUNNING
            self._update_job(job)
            # Use a placeholder until the process is actually started, so that
            # we do not exceed the quota due to races.
            self.running_jobs[job.identifier] = None

            d = self._run_crawler(job.project, job.spider, job.identifier)

            #-------------------------------------------------------------------
            # Error starting the job
            #-------------------------------------------------------------------
            def spawn_errback(error, job):
                self.counter_failure += 1
                job.status = Status.FAILED
                self._update_job(job)
                self.log.error('Unable to start job {}: {}'.format(
                    job.identifier, exc_repr(error.value)))
                del self.running_jobs[job.identifier]

            #-------------------------------------------------------------------
            # Job started successfully
            #-------------------------------------------------------------------
            def spawn_callback(value, job):
                # Put the process object and the finish deferred in the
                # dictionary
                running_job = RunningJob(value[0], value[1], datetime.now())
                self.running_jobs[job.identifier] = running_job
                self.log.info('Job {} started successfully'.format(
                    job.identifier))

                #---------------------------------------------------------------
                # Finish things up
                #---------------------------------------------------------------
                def finished_callback(exit_code):
                    if exit_code == 0:
                        self.counter_success += 1
                        job.status = Status.SUCCESSFUL
                    else:
                        self.counter_failure += 1
                        job.status = Status.FAILED

                    rj = self.running_jobs[job.identifier]
                    job.duration = (datetime.now() - rj.time_started).seconds
                    msg = "Job {} exited with code {}".format(job.identifier,
                                                              exit_code)
                    self.log.info(msg)
                    self._update_job(job)
                    del self.running_jobs[job.identifier]
                    return exit_code

                value[1].addCallback(finished_callback)

            d.addCallbacks(spawn_callback, spawn_errback,
                           callbackArgs=(job,), errbackArgs=(job,))

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def wait_for_starting_jobs(self):
        """
        Wait until all the crawling processes in the job slots started.

        :return: A deferred triggered when all the processes have started
        """
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
        """
        Wait for all the running jobs to finish.

        :param cancel: If `True` send a `SIGTERM` signal to each of the running
                       crawlers
        :return:       A deferred triggered when all the running jobs have
                       finished
        """
        yield self.wait_for_starting_jobs()

        #-----------------------------------------------------------------------
        # Send SIGTERM if requested
        #-----------------------------------------------------------------------
        if cancel:
            for job_id in self.running_jobs:
                rj = self.running_jobs[job_id]
                rj.process.signalProcess('TERM')

        #-----------------------------------------------------------------------
        # Wait for the jobs to finish
        #-----------------------------------------------------------------------
        to_finish = []
        for job_id in self.running_jobs:
            rj = self.running_jobs[job_id]
            to_finish.append(rj.finished_d)

        for d in to_finish:
            yield d

    #---------------------------------------------------------------------------
    @inlineCallbacks
    def cancel_job(self, job_id):
        """
        Cancel a job.

        :param job_id: A string identifier of a job
        :return:       A deferred that is triggered when the job is cancelled
        """
        job = self.schedule.get_job(job_id)
        self.log.info('Canceling: {}'.format(str(job)))

        #-----------------------------------------------------------------------
        # Scheduled
        #-----------------------------------------------------------------------
        if job.status == Status.SCHEDULED:
            job.status = Status.CANCELED
            self._update_job(job)
            self.scheduler.cancel_job(self.scheduled_jobs[job_id])
            del self.scheduled_jobs[job_id]

        #-----------------------------------------------------------------------
        # Pending
        #-----------------------------------------------------------------------
        elif job.status == Status.PENDING:
            job.status = Status.CANCELED
            self._update_job(job)

        #-----------------------------------------------------------------------
        # Running
        #-----------------------------------------------------------------------
        elif job.status == Status.RUNNING:
            while True:
                if job_id not in self.running_jobs:
                    raise ValueError('Job {} is not active'.format(job_id))
                if self.running_jobs[job_id] is None:
                    yield twisted_sleep(0.1)  # wait until the job starts
                else:
                    break
            rj = self.running_jobs[job_id]
            rj.process.signalProcess('TERM')
            yield rj.finished_d
            self.counter_failure -= 1
            self.counter_cancel += 1
            job.status = Status.CANCELED
            job.duration = (datetime.now() - rj.time_started).seconds
            self._update_job(job)

        #-----------------------------------------------------------------------
        # Not active
        #-----------------------------------------------------------------------
        else:
            raise ValueError('Job {} is not active'.format(job_id))

    #---------------------------------------------------------------------------
    def purge_completed_jobs(self):
        """
        Purge all the old jobs exceeding the completed cap.
        """
        old_jobs = self.get_completed_jobs()[self.completed_cap:]

        if len(old_jobs):
            self.log.info('Purging {} old jobs'.format(len(old_jobs)))

        for job in old_jobs:
            self.dispatch_event(Event.JOB_REMOVE, job.identifier)
            self.schedule.remove_job(job.identifier)
            for log_type in ['.out', '.err']:
                log_file = os.path.join(self.log_dir, job.identifier + log_type)
                if os.path.exists(log_file):
                    os.remove(log_file)

    #---------------------------------------------------------------------------
    def remove_project(self, name):
        """
        Remove the project
        """
        #-----------------------------------------------------------------------
        # Consistency checks
        #-----------------------------------------------------------------------
        if name not in self.projects:
            raise ValueError('No such project: "{}"'.format(name))

        sched_jobs = self.schedule.get_scheduled_jobs(name)
        if len(sched_jobs) != 0:
            msg = 'There are {} scheduled spiders for project "{}"'.format(
                len(sched_jobs), name)
            self.log.info('Failed to remove project "{}": {}'.format(
                name, msg))
            raise ValueError(msg)

        #-----------------------------------------------------------------------
        # Remove the project
        #-----------------------------------------------------------------------
        os.remove(self.projects[name].archive)
        del self.projects[name]
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.projects, f)

        self.log.info('Project "{}" removed'.format(name))
        self.dispatch_event(Event.PROJECT_REMOVE, name)

    #---------------------------------------------------------------------------
    def _update_job(self, job):
        self.dispatch_event(Event.JOB_UPDATE, job)
        self.schedule.commit_job(job)

    #---------------------------------------------------------------------------
    def add_event_listener(self, listener):
        """
        Add an event listener.
        """
        self.listeners.add(listener)

    #---------------------------------------------------------------------------
    def remove_event_listener(self, listener):
        """
        Remove the event listener.
        """
        self.listeners.remove(listener)

    #---------------------------------------------------------------------------
    def dispatch_event(self, event_type, event_data):
        """
        Dispatch an event to all the listeners.
        """
        for listener in self.listeners:
            listener(event_type, event_data)

    #---------------------------------------------------------------------------
    def dispatch_periodic_events(self):
        """
        Dispatch periodic events if necessary.
        """
        #-----------------------------------------------------------------------
        # Daemon status - send the event either every minute or whenever
        # the memory usage crossed a megabyte boundary
        #-----------------------------------------------------------------------
        mem_usage = psutil.Process(os.getpid()).memory_info().rss
        mem_usage = float(mem_usage) / 1024. / 1024.
        mem_usage = int(mem_usage)
        now = time.time()
        if self.mem_usage is None or now - self.mem_usage_ts >= 60 or \
                abs(self.mem_usage - mem_usage) >= 1:
            self.mem_usage = mem_usage
            self.mem_usage_ts = now
            self.dispatch_event(Event.DAEMON_STATUS_CHANGE, None)
