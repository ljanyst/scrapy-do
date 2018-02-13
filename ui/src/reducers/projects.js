//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 13.02.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import {
  PROJECT_PUSH, PROJECT_REMOVE, PROJECT_LIST_SET
} from '../actions/projects';

const projectsState = {};

export function projectsReducer(state = projectsState, action) {
  switch(action.type) {

  case PROJECT_PUSH:
    return {
      ...state,
      [action.name]: {
        name: action.name,
        spiders: action.spiders
      }
    };

  case PROJECT_REMOVE:
    let newState = Object.assign(state);
    delete newState[action.name];
    return newState;

  case PROJECT_LIST_SET:
    return action.projects.reduce((acc, current) => {
      acc[current.name] = current;
      return acc;
    }, {});

  default:
    return state;
  }
}
