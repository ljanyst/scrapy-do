//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 13.02.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import { JOB_LIST_SET, JOB_UPDATE, JOB_REMOVE } from '../actions/jobs';

const jobsState = {};

function filterJob(state, jobId) {
  let newState = Object.assign(state);
  if('ACTIVE' in newState)
    delete newState['ACTIVE'][jobId];
  if('COMPLETED' in newState)
    delete newState['COMPLETED'][jobId];
  return newState;
}

function statusToListName(status) {
  if(status === 'SCHEDULED' || status === 'PENDING' || status === 'RUNNING')
    return 'ACTIVE';
  return 'COMPLETED';
}

export function jobsReducer(state = jobsState, action) {
  switch(action.type) {

  case JOB_LIST_SET:
    let jobs =  action.jobs.reduce((acc, current) => {
      acc[current.identifier] = current;
      return acc;
    }, {});
    return {
      ...state,
      [action.status]: jobs
    };

  case JOB_REMOVE:
    return filterJob(state, action.jobId);

  case JOB_UPDATE:
    let newState = filterJob(state, action.job.identifier);
    let listName = statusToListName(action.job.status);
    newState[listName][action.job.identifier] = action.job;
    return newState;

  default:
    return state;
  }
}
