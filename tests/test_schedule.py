#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   02.12.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import unittest
import tempfile
import shutil
import glob
import os

from scrapy_do.schedule import Schedule, Job, Status, Actor


#-------------------------------------------------------------------------------
class ScheduleTests(unittest.TestCase):

    #---------------------------------------------------------------------------
    def setUp(self):
        self.schedule = Schedule()
        self.job1 = Job(status=Status.SCHEDULED, actor=Actor.USER,
                        schedule='every tuesday at 12:12', project='testproj1',
                        spider='testspider1')
        self.job2 = Job(status=Status.SCHEDULED, actor=Actor.USER,
                        schedule='every 2 to 3 hours', project='testproj2',
                        spider='testspider2')
        self.job3 = Job(status=Status.PENDING, actor=Actor.SCHEDULER,
                        project='testproj3', spider='testspider3')
        self.job4 = Job(status=Status.RUNNING, actor=Actor.SCHEDULER,
                        project='testproj4', spider='testspider4')
        self.job5 = Job(status=Status.CANCELED, actor=Actor.SCHEDULER,
                        project='testproj5', spider='testspider5')
        self.job6 = Job(status=Status.CANCELED, actor=Actor.SCHEDULER,
                        project='testproj6', spider='testspider6')
        self.job7 = Job(status=Status.CANCELED, actor=Actor.SCHEDULER,
                        project='testproj7', spider='testspider7')
        self.job8 = Job(status=Status.CANCELED, actor=Actor.SCHEDULER,
                        project='testproj8', spider='testspider8',
                        title='testproj8', payload='{"foo": "bar"}')

        self.schedule.add_job(self.job1)
        self.schedule.add_job(self.job2)
        self.schedule.add_job(self.job3)
        self.schedule.add_job(self.job4)
        self.schedule.add_job(self.job5)
        self.schedule.add_job(self.job6)
        self.schedule.add_job(self.job7)
        self.schedule.add_job(self.job8)

    #---------------------------------------------------------------------------
    def compare_jobs(self, job1, job2):
        self.assertEqual(job1.identifier, job2.identifier)
        self.assertEqual(job1.status, job2.status)
        self.assertEqual(job1.actor, job2.actor)
        self.assertEqual(job1.schedule, job2.schedule)
        self.assertEqual(job1.project, job2.project)
        self.assertEqual(job1.spider, job2.spider)
        self.assertEqual(job1.timestamp, job2.timestamp)
        self.assertEqual(job1.duration, job2.duration)
        self.assertEqual(job1.title, job2.title)
        self.assertEqual(job1.payload, job2.payload)

    #---------------------------------------------------------------------------
    def test_upgrade_from_v1_to_v2(self):
        db_file_orig = os.path.join(os.path.dirname(__file__),
                                    'schedule-v1.db')
        tmp_dir = tempfile.mkdtemp()
        db_file_test = os.path.join(tmp_dir, 'schedule-v1.db')
        shutil.copyfile(db_file_orig, db_file_test)

        schedule = Schedule(db_file_test)
        jobs = schedule.get_active_jobs()
        for job in jobs:
            self.assertEqual(job.title, job.spider)

        self.assertEqual(int(self.schedule.get_metadata('version')), 2)

        lst = glob.glob(db_file_test + '.bak*')
        self.assertEqual(len(lst), 1)
        shutil.rmtree(tmp_dir)

    #---------------------------------------------------------------------------
    def test_retrieval(self):
        scheduled_jobs = self.schedule.get_jobs(Status.SCHEDULED)
        pending_jobs = self.schedule.get_jobs(Status.PENDING)
        self.assertEqual(len(scheduled_jobs), 2)
        self.assertEqual(len(pending_jobs), 1)
        self.compare_jobs(self.job3, pending_jobs[0])

        job = self.schedule.get_job(scheduled_jobs[0].identifier)
        self.compare_jobs(job, scheduled_jobs[0])

        with self.assertRaises(ValueError):
            self.schedule.get_job(identifier=scheduled_jobs[0].identifier + 'a')

        active_jobs = self.schedule.get_active_jobs()
        completed_jobs = self.schedule.get_completed_jobs()

        for job in active_jobs:
            self.assertIn(job.status,
                          [Status.SCHEDULED, Status.PENDING, Status.RUNNING])
        for job in completed_jobs:
            self.assertIn(job.status,
                          [Status.CANCELED, Status.SUCCESSFUL, Status.FAILED])

        sched_proj2 = self.schedule.get_scheduled_jobs('testproj2')
        for job in sched_proj2:
            self.assertEqual(job.project, 'testproj2')
            self.assertEqual(job.status, Status.SCHEDULED)

    #---------------------------------------------------------------------------
    def test_change(self):
        pending_jobs = self.schedule.get_jobs(Status.PENDING)
        job = pending_jobs[0]
        job.status = Status.RUNNING
        self.assertTrue(job.timestamp > self.job3.timestamp)
        self.schedule.commit_job(job)
        running_jobs = self.schedule.get_jobs(Status.RUNNING)
        pending_jobs = self.schedule.get_jobs(Status.PENDING)
        self.assertEqual(len(running_jobs), 2)
        self.assertEqual(len(pending_jobs), 0)
        self.compare_jobs(job, running_jobs[0])

    #---------------------------------------------------------------------------
    def test_remove(self):
        scheduled_jobs = self.schedule.get_jobs(Status.SCHEDULED)
        self.assertEqual(len(scheduled_jobs), 2)
        job = scheduled_jobs[0]
        self.schedule.remove_job(job.identifier)
        scheduled_jobs = self.schedule.get_jobs(Status.SCHEDULED)
        self.assertEqual(len(scheduled_jobs), 1)

    #---------------------------------------------------------------------------
    def test_dict(self):
        job = self.schedule.get_jobs(Status.SCHEDULED)[0]
        job_data = job.to_dict()
        keys = ['identifier', 'status', 'actor', 'project', 'spider',
                'timestamp', 'duration']
        for k in keys:
            self.assertIn(k, job_data)
        self.assertIsInstance(job_data['timestamp'], str)
        self.assertIsInstance(job_data['status'], str)
        self.assertIsInstance(job_data['actor'], str)

    #---------------------------------------------------------------------------
    def test_metadata(self):
        self.assertEqual(int(self.schedule.get_metadata('version')), 2)
        with self.assertRaises(KeyError):
            self.schedule.get_metadata('foo')
