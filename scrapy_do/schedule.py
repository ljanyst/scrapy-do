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
import shutil
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
    description = TimeStamper('_description')
    duration = TimeStamper('_duration')
    payload = TimeStamper('_payload')

    #---------------------------------------------------------------------------
    def __init__(self, status=None, actor=None, schedule=None,
                 project=None, spider=None, timestamp=None, duration=None,
                 description='', payload='{}'):
        self.identifier = str(uuid.uuid4())

        self._status = status
        self._actor = actor
        self._schedule = schedule
        self._project = project
        self._spider = spider
        self._description = description
        self.timestamp = timestamp or datetime.now()
        self._duration = duration
        self._payload = payload

    #---------------------------------------------------------------------------
    def __str__(self):
        s = 'Job[id="{}", actor="{}", schedule="{}", project="{}", '
        s += 'spider="{}", description="{}"]'
        s = s.format(self.identifier, self.actor.name, self.schedule,
                     self.project, self.spider, self.description)
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
            'description': self.description,
            'timestamp': str(self.timestamp),
            'duration': self.duration,
            'payload': self.payload
        }
        return d


#-------------------------------------------------------------------------------
def _record_to_job(x):
    job = Job(status=Status(x[1]), actor=Actor(x[2]), schedule=x[3],
              project=x[4], spider=x[5], timestamp=dateutil.parser.parse(x[6]),
              duration=x[7], description=x[8], payload=x[9])
    job.identifier = x[0]
    return job


#-------------------------------------------------------------------------------
class Schedule:
    """
    A persistent database of jobs.

    :param database: A file name where the database will be stored
    """

    CURRENT_VERSION = 2

    #---------------------------------------------------------------------------
    def __init__(self, database=None):
        #-----------------------------------------------------------------------
        # Create the database
        #-----------------------------------------------------------------------
        self.database = database or ':memory:'
        self.db = sqlite3.connect(self.database,
                                  detect_types=sqlite3.PARSE_DECLTYPES)

        #-----------------------------------------------------------------------
        # Create the metadata table if it does not exist
        #-----------------------------------------------------------------------
        query = 'CREATE TABLE IF NOT EXISTS schedule_metadata (' \
                'key VARCHAR(255) PRIMARY KEY ON CONFLICT IGNORE, ' \
                'value VARCHAR(255) NOT NULL ' \
                ')'
        self.db.execute(query)
        self.db.commit()

        query = 'SELECT * FROM schedule_metadata WHERE key="version"'
        response = self.db.execute(query)
        response = dict(response)

        if 'version' in response:
            self._open_database(int(response['version']))
        else:
            self._create_database()

    #---------------------------------------------------------------------------
    def _upgrade_v1_to_v2(self):
        query = 'ALTER TABLE schedule ADD description VARCHAR(512) DEFAULT "" '
        query += 'NOT NULL;'
        self.db.execute(query)

        query = 'ALTER TABLE schedule ADD payload VARCHAR(4096) DEFAULT "{}" '
        query += 'NOT NULL;'
        self.db.execute(query)
        self.db.commit()

    #---------------------------------------------------------------------------
    def _open_database(self, version):
        bak_file = self.database + '.bak.'
        bak_file += datetime.now().strftime('%Y%m%d-%H%M%S')
        shutil.copyfile(self.database, bak_file)
        upgraders = {}
        upgraders[1] = self._upgrade_v1_to_v2
        for v in range(version, self.CURRENT_VERSION):
            upgraders[v]()

        query = 'UPDATE schedule_metadata ' \
                'SET value = ?' \
                'WHERE key = "version";'
        self.db.execute(query, (str(self.CURRENT_VERSION),))
        self.db.commit()

    #---------------------------------------------------------------------------
    def _create_database(self):
        query = 'INSERT INTO schedule_metadata ' \
                '(key, value) values ("version", ?)'
        self.db.execute(query, (str(self.CURRENT_VERSION),))

        #-----------------------------------------------------------------------
        # Create the main table
        #-----------------------------------------------------------------------
        query = "CREATE TABLE IF NOT EXISTS schedule (" \
                "identifier VARCHAR(36) PRIMARY KEY, " \
                "status INTEGER NOT NULL, " \
                "actor INTEGER NOT NULL, " \
                "schedule VARCHAR(255), " \
                "project VARCHAR(255) NOT NULL, " \
                "spider VARCHAR(255) NOT NULL, " \
                "timestamp DATETIME NOT NULL, " \
                "duration INTEGER," \
                "description VARCHAR(512) NOT NULL," \
                "payload VARCHAR(4096) NOT NULL" \
                ")"
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
        query = "SELECT * FROM schedule WHERE status=? ORDER BY timestamp DESC"
        response = self.db.execute(query, (job_status.value, ))
        return [_record_to_job(rec) for rec in response]

    #---------------------------------------------------------------------------
    def get_active_jobs(self):
        """
        Retrieve all the active jobs. Ie. all the jobs whose status is one of
        the following: :data:`SCHEDULED <Status.SCHEDULED>`,
        :data:`PENDING <Status.PENDING>`, or :data:`RUNNING <Status.RUNNING>`.
        """
        query = "SELECT * FROM schedule WHERE " \
                "status=1 OR status=2 OR status=3 "\
                "ORDER BY timestamp DESC"
        response = self.db.execute(query)
        return [_record_to_job(rec) for rec in response]

    #---------------------------------------------------------------------------
    def get_completed_jobs(self):
        """
        Retrieve all the completed jobs. Ie. all the jobs whose status is one of
        the  following: :data:`SUCCESSFUL <Status.SUCCESSFUL>`,
        :data:`FAILED <Status.FAILED>`, or :data:`CANCELED <Status.CANCELED>`.
        """
        query = "SELECT * FROM schedule WHERE " \
                "status=4 OR status=5 OR status=6 "\
                "ORDER BY timestamp DESC"
        response = self.db.execute(query)
        return [_record_to_job(rec) for rec in response]

    #---------------------------------------------------------------------------
    def get_scheduled_jobs(self, project):
        """
        Retrieve all the scheduled jobs for the given project.
        """
        query = "SELECT * FROM schedule WHERE " \
                "status=1 AND project=?" \
                "ORDER BY timestamp DESC"
        response = self.db.execute(query, (project, ))
        return [_record_to_job(rec) for rec in response]

    #---------------------------------------------------------------------------
    def get_job(self, identifier):
        """
        Retrieve a job by id

        :param identifier: A string identifier of the job
        """
        query = "SELECT * FROM schedule WHERE identifier=?"
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
        query = "INSERT INTO schedule" \
                "(identifier, status, actor, schedule, project, spider, " \
                "timestamp, duration, description, payload) " \
                "values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        self.db.execute(query, (job.identifier, job.status.value,
                                job.actor.value, job.schedule, job.project,
                                job.spider, job.timestamp, job.duration,
                                job.description, job.payload))
        self.db.commit()

    #---------------------------------------------------------------------------
    def commit_job(self, job):
        """
        Modify an existing job

        :param job: A :class:`Job <Job>` object
        """
        query = "REPLACE INTO schedule" \
                "(identifier, status, actor, schedule, project, spider, " \
                "timestamp, duration, description, payload) " \
                "values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        self.db.execute(query, (job.identifier, job.status.value,
                                job.actor.value, job.schedule, job.project,
                                job.spider, job.timestamp, job.duration,
                                job.description, job.payload))
        self.db.commit()

    #---------------------------------------------------------------------------
    def remove_job(self, job_id):
        """
        Remove a job from the database

        :param identifier: A string identifier of the job
        """
        query = "DELETE FROM schedule WHERE identifier=?"
        self.db.execute(query, (job_id,))
        self.db.commit()
