//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 30.01.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component } from 'react';
import { connect } from 'react-redux';
import moment from 'moment-timezone';

//------------------------------------------------------------------------------
// Dashboard
//------------------------------------------------------------------------------
class Dashboard extends Component {
  render() {
    const serverTime = moment.unix(this.props.time)
          .tz('Europe/Zurich').format('YYYY-MM-DD HH:mm');
    return(
      <div className='col-md-6 col-md-offset-3'>
        <div className='dashboard-content'>
          <img src='scrapy-do-logo.png' alt='Scrapy-Do Logo' />
          <p>Version {this.props.daemonVersion} @ {this.props.hostname}</p>
          <p>Server time: {serverTime} ({this.props.timezone})</p>
          <p>
            Uptime: {this.props.uptime} | CPU Usage: {this.props.cpuUsage}% |
            Memory Usage: {this.props.memoryUsage}MB
          </p>
        </div>
      </div>
    );
  }
}

//------------------------------------------------------------------------------
// The redux connection
//------------------------------------------------------------------------------
function mapStateToProps(state, ownProps) {
  return {
    ...state.status
  };
}

function mapDispatchToProps(dispatch) {
  return {};
}

export default connect(mapStateToProps, mapDispatchToProps)(Dashboard);
