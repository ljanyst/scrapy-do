//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 30.01.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component } from 'react';

class JobList extends Component {
  render() {
    return(
      <div>
        JobList {this.props.match.params.status}
      </div>
    );
  }
}

export default JobList;
