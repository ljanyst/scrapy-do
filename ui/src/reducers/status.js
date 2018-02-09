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
  memoryUsage: null,
  cpuUsage: null,
  time: null,
  timezone: null,
  hostname: null,
  startTime: null,
  deamonVersion: null,
  projects: null,
  spiders: null,
  jobsRun: null,
  jobsSuccessful: null,
  jobsFailed: null,
  jobsCanceled: null,
  jobsScheduled: null
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
      startTime: action.startTime,
      deamonVersion: action.daemonVersion
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
