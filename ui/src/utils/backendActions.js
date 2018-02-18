//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 17.02.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import { backend } from './Backend';

//------------------------------------------------------------------------------
// Remove project
//------------------------------------------------------------------------------
export function projectRemove(name) {
  return backend.sendMessage({
    action: 'PROJECT_REMOVE',
    name
  });
}
