//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 09.02.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import {
  DAEMON_STATUS_SET, PROJECTS_STATUS_SET, JOBS_STATUS_SET
} from '../actions/status';

const statusState = {
  memoryUsage: 0,
  cpuUsage: 0,
  time: 0,
  timezone: 'UTC',
  hostname: 'unknown',
  uptime: '0m',
  daemonVersion: '0.0.0',
  projects: 0,
  spiders: 0,
  jobsRun: 0,
  jobsSuccessful: 0,
  jobsFailed: 0,
  jobsCanceled: 0,
  jobsScheduled: 0
};

export function statusReducer(state = statusState, action) {
  switch(action.type) {

  case DAEMON_STATUS_SET:
    return {
      ...state,
      memoryUsage: action.memoryUsage,
      cpuUsage: action.cpuUsage,
      time: action.time,
      timezone: action.timezone,
      hostname: action.hostname,
      uptime: action.uptime,
      daemonVersion: action.daemonVersion
    };

  case PROJECTS_STATUS_SET:
    return {
      ...state,
      projects: action.projects,
      spiders: action.spiders
    };

  case JOBS_STATUS_SET:
    return {
      ...state,
      jobsRun: action.jobsRun,
      jobsSuccessful: action.jobsSuccessful,
      jobsFailed: action.jobsFailed,
      jobsCanceled: action.jobsCanceled,
      jobsScheduled: action.jobsScheduled
    };

  default:
    return state;
  }
}
