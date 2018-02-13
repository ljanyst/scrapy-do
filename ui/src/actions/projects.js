//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 13.02.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

export const PROJECT_PUSH = 'PROJECT_PUSH';
export const PROJECT_REMOVE = 'PROJECT_REMOVE';
export const PROJECT_LIST_SET = 'PROJECT_LIST_SET';

export function projectPush(name, spiders) {
  return {
    type: PROJECT_PUSH,
    name,
    spiders
  };
}

export function projectRemove(name) {
  return {
    type: PROJECT_REMOVE,
    name
  };
}

export function projectListSet(projects) {
  return {
    type: PROJECT_LIST_SET,
    projects
  };
}
