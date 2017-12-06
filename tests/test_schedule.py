#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   02.12.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import unittest

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
                        project='testproj2', spider='testspider2')

        self.schedule.add_job(self.job1)
        self.schedule.add_job(self.job2)
        self.schedule.add_job(self.job3)

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

    #---------------------------------------------------------------------------
    def test_retrieval(self):
        scheduled_jobs = self.schedule.get_jobs(Status.SCHEDULED)
        pending_jobs = self.schedule.get_jobs(Status.PENDING)
        self.assertEqual(len(scheduled_jobs), 2)
        self.assertEqual(len(pending_jobs), 1)
        self.compare_jobs(self.job3, pending_jobs[0])

        job = self.schedule.get_job(scheduled_jobs[0].identifier)
        self.compare_jobs(job, scheduled_jobs[0])

        with self.assertRaises(KeyError):
            self.schedule.get_job(identifier=scheduled_jobs[0].identifier + 'a')

    #---------------------------------------------------------------------------
    def test_change(self):
        pending_jobs = self.schedule.get_jobs(Status.PENDING)
        job = pending_jobs[0]
        job.status = Status.RUNNING
        self.assertTrue(job.timestamp > self.job3.timestamp)
        self.schedule.commit_job(job)
        running_jobs = self.schedule.get_jobs(Status.RUNNING)
        pending_jobs = self.schedule.get_jobs(Status.PENDING)
        self.assertEqual(len(running_jobs), 1)
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
