//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 13.02.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import { JOB_LIST_SET } from '../actions/jobs';

const jobsState = {};

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

  default:
    return state;
  }
}
