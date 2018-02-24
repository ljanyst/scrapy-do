#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   02.12.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

"""
Functionality related to the database of jobs.
"""

import dateutil.parser
import sqlite3
import uuid

from scrapy_do.utils import TimeStamper
from datetime import datetime
from enum import Enum


#-------------------------------------------------------------------------------
class Status(Enum):
    """
    Status of the job.
    """
    SCHEDULED = 1
    PENDING = 2
    RUNNING = 3
    CANCELED = 4
    SUCCESSFUL = 5
    FAILED = 6


#-------------------------------------------------------------------------------
class Actor(Enum):
    """
    An entity responsible for job creation.
    """
    SCHEDULER = 1
    USER = 2


#-------------------------------------------------------------------------------
class Job:
    """
    A bin for all the parameters of a job.
    """

    status = TimeStamper('_status')
    actor = TimeStamper('_actor')
    schedule = TimeStamper('_schedule')
    project = TimeStamper('_project')
    spider = TimeStamper('_spider')
    duration = TimeStamper('_duration')

    #---------------------------------------------------------------------------
    def __init__(self, status=None, actor=None, schedule=None,
                 project=None, spider=None, timestamp=None, duration=None):
        self.identifier = str(uuid.uuid4())
        self._status = status
        self._actor = actor
        self._schedule = schedule
        self._project = project
        self._spider = spider
        self.timestamp = timestamp or datetime.now()
        self._duration = duration

    #---------------------------------------------------------------------------
    def __str__(self):
        s = 'Job[id="{}", actor="{}", schedule="{}", project="{}", spider="{}"]'
        s = s.format(self.identifier, self.actor.name, self.schedule,
                     self.project, self.spider)
        return s

    #---------------------------------------------------------------------------
    def to_dict(self):
        """
        Return all the parameters of the job as a dictionary
        """
        d = {
            'identifier': self.identifier,
            'status': self.status.name,
            'actor': self.actor.name,
            'schedule': self.schedule,
            'project': self.project,
            'spider': self.spider,
            'timestamp': str(self.timestamp),
            'duration': self.duration
        }
        return d


#-------------------------------------------------------------------------------
def _record_to_job(x):
    job = Job(status=Status(x[1]), actor=Actor(x[2]), schedule=x[3],
              project=x[4], spider=x[5], timestamp=dateutil.parser.parse(x[6]),
              duration=x[7])
    job.identifier = x[0]
    return job


#-------------------------------------------------------------------------------
class Schedule:
    """
    A persistent database of jobs.

    :param database: A file name where the database will be stored
    :param table:    Name of the table containing the schedule
    """

    #---------------------------------------------------------------------------
    def __init__(self, database=None, table='schedule'):
        #-----------------------------------------------------------------------
        # Create the database and the main table
        #-----------------------------------------------------------------------
        self.database = database or ':memory:'
        self.table = table
        self.db = sqlite3.connect(self.database,
                                  detect_types=sqlite3.PARSE_DECLTYPES)

        query = "CREATE TABLE IF NOT EXISTS {table} (" \
                "identifier VARCHAR(36) PRIMARY KEY, " \
                "status INTEGER NOT NULL, " \
                "actor INTEGER NOT NULL, " \
                "schedule VARCHAR(255), " \
                "project VARCHAR(255) NOT NULL, " \
                "spider VARCHAR(255) NOT NULL, " \
                "timestamp DATETIME NOT NULL, " \
                "duration INTEGER" \
                ")"
        query = query.format(table=self.table)
        self.db.execute(query)

        #-----------------------------------------------------------------------
        # Create the metadata table
        #-----------------------------------------------------------------------
        query = 'CREATE TABLE IF NOT EXISTS schedule_metadata (' \
                'key VARCHAR(255) PRIMARY KEY ON CONFLICT IGNORE, ' \
                'value VARCHAR(255) NOT NULL ' \
                ')'
        self.db.execute(query)

        query = 'INSERT INTO schedule_metadata ' \
                '(key, value) values ("version", "1") '
        self.db.execute(query)
        self.db.commit()

    #---------------------------------------------------------------------------
    def get_metadata(self, key):
        """
        Retrieve the matadata info with a given key
        """
        query = "SELECT * FROM schedule_metadata WHERE key=?"
        response = self.db.execute(query, (key, ))
        response = dict(response)
        return response[key]

    #---------------------------------------------------------------------------
    def get_jobs(self, job_status):
        """
        Retrieve a list of jobs with a given status

        :param job_status: One of :class:`statuses <Status>`
        """
        query = "SELECT * FROM {table} WHERE status=? ORDER BY timestamp DESC"
        query = query.format(table=self.table)
        response = self.db.execute(query, (job_status.value, ))
        return [_record_to_job(rec) for rec in response]

    #---------------------------------------------------------------------------
    def get_active_jobs(self):
        """
        Retrieve all the active jobs. Ie. all the jobs whose status is one of
        the following: :data:`SCHEDULED <Status.SCHEDULED>`,
        :data:`PENDING <Status.PENDING>`, or :data:`RUNNING <Status.RUNNING>`.
        """
        query = "SELECT * FROM {table} WHERE " \
                "status=1 OR status=2 OR status=3 "\
                "ORDER BY timestamp DESC"
        query = query.format(table=self.table)
        response = self.db.execute(query)
        return [_record_to_job(rec) for rec in response]

    #---------------------------------------------------------------------------
    def get_completed_jobs(self):
        """
        Retrieve all the completed jobs. Ie. all the jobs whose status is one of
        the  following: :data:`SUCCESSFUL <Status.SUCCESSFUL>`,
        :data:`FAILED <Status.FAILED>`, or :data:`CANCELED <Status.CANCELED>`.
        """
        query = "SELECT * FROM {table} WHERE " \
                "status=4 OR status=5 OR status=5 "\
                "ORDER BY timestamp DESC"
        query = query.format(table=self.table)
        response = self.db.execute(query)
        return [_record_to_job(rec) for rec in response]

    #---------------------------------------------------------------------------
    def get_scheduled_jobs(self, project):
        """
        Retrieve all the scheduled jobs for the given project.
        """
        query = "SELECT * FROM {table} WHERE " \
                "status=1 AND project=?" \
                "ORDER BY timestamp DESC"
        query = query.format(table=self.table)
        response = self.db.execute(query, (project, ))
        return [_record_to_job(rec) for rec in response]

    #---------------------------------------------------------------------------
    def get_job(self, identifier):
        """
        Retrieve a job by id

        :param identifier: A string identifier of the job
        """
        query = "SELECT * FROM {table} WHERE identifier=?"
        query = query.format(table=self.table)
        response = self.db.execute(query, (identifier, ))
        rec = response.fetchone()
        if rec is None:
            raise ValueError('No such job: "{}"'.format(identifier))
        return _record_to_job(rec)

    #---------------------------------------------------------------------------
    def add_job(self, job):
        """
        Add a job to the database

        :param job: A :class:`Job <Job>` object
        """
        query = "INSERT INTO {table}" \
                "(identifier, status, actor, schedule, project, spider, " \
                "timestamp, duration) " \
                "values (?, ?, ?, ?, ?, ?, ?, ?)"
        query = query.format(table=self.table)
        self.db.execute(query, (job.identifier, job.status.value,
                                job.actor.value, job.schedule, job.project,
                                job.spider, job.timestamp, job.duration))
        self.db.commit()

    #---------------------------------------------------------------------------
    def commit_job(self, job):
        """
        Modify an existing job

        :param job: A :class:`Job <Job>` object
        """
        query = "REPLACE INTO {table}" \
                "(identifier, status, actor, schedule, project, spider, " \
                "timestamp, duration) " \
                "values (?, ?, ?, ?, ?, ?, ?, ?)"
        query = query.format(table=self.table)
        self.db.execute(query, (job.identifier, job.status.value,
                                job.actor.value, job.schedule, job.project,
                                job.spider, job.timestamp, job.duration))
        self.db.commit()

    #---------------------------------------------------------------------------
    def remove_job(self, job_id):
        """
        Remove a job from the database

        :param identifier: A string identifier of the job
        """
        query = "DELETE FROM {table} WHERE identifier=?"
        query = query.format(table=self.table)
        self.db.execute(query, (job_id,))
        self.db.commit()
