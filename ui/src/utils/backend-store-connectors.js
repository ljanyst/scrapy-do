//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 09.02.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import { store } from '../';
import { Backend } from './Backend';
import {
  daemonStatusSet, projectsStatusSet, jobsStatusSet
} from '../actions/status';
import { projectListSet } from '../actions/projects';

//------------------------------------------------------------------------------
// Make backend events change the state of the stare
//------------------------------------------------------------------------------
export const messageStoreEvent = (event, data) => {
  if(event !== Backend.MSG_RECEIVED)
    return;

  switch(data.type) {
  case 'DAEMON_STATUS':
    store.dispatch(daemonStatusSet(data));
    break;
  case 'PROJECTS_STATUS':
    store.dispatch(projectsStatusSet(data));
    break;
  case 'JOBS_STATUS':
    store.dispatch(jobsStatusSet(data));
    break;
  case 'PROJECT_LIST':
    store.dispatch(projectListSet(data.projects));
    break;

  default:
    break;
  }
};
