//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 09.02.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

export const DAEMON_STATUS_SET = 'DAEMON_STATUS_SET';
export const PROJECTS_STATUS_SET = 'PROJECTS_STATUS_SET';
export const JOBS_STATUS_SET = 'JOBS_STATUS_SET';

export function daemonStatusSet(status) {
  const {
    memoryUsage, cpuUsage, time, timezone, hostname, uptime, daemonVersion
  } = status;
  return {
    type: DAEMON_STATUS_SET,
    memoryUsage,
    cpuUsage,
    time,
    timezone,
    hostname,
    uptime,
    daemonVersion
  };
}

export function projectsStatusSet(status) {
  const { projects, spiders } = status;
  return {
    type: PROJECTS_STATUS_SET,
    projects,
    spiders
  };
}

export function jobsStatusSet(status) {
  const {
    jobsRun, jobsSuccessful, jobsFailed, jobsCanceled, jobsScheduled
  } = status;
  return {
    type: JOBS_STATUS_SET,
    jobsRun,
    jobsSuccessful,
    jobsFailed,
    jobsCanceled,
    jobsScheduled
  };
}
