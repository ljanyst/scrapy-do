//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 30.01.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component } from 'react';
import { Table } from 'react-bootstrap';
import { connect } from 'react-redux';
import moment from 'moment-timezone';

//------------------------------------------------------------------------------
// Dashboard
//------------------------------------------------------------------------------
class Dashboard extends Component {
  render() {
    const serverTime = moment.unix(this.props.time)
          .tz(this.props.timezone).format('YYYY-MM-DD HH:mm');
    return(
      <div className='col-md-6 col-md-offset-3'>
        <div className='dashboard-content'>
          <img src='scrapy-do-logo.png' alt='Scrapy-Do Logo' />
          <div className='text-summary'>
            <div>Version {this.props.daemonVersion} @ {this.props.hostname}</div>
            <div>Server time: {serverTime} ({this.props.timezone})</div>
            <div>
              Uptime: {this.props.uptime} | CPU Usage: {this.props.cpuUsage}% |
              Memory Usage: {this.props.memoryUsage}MB
            </div>
            <div>
              Projects: {this.props.projects} |
              Spiders: {this.props.spiders}
            </div>

            <div className='jobs-summary'>
              <Table striped bordered size="sm">
                <thead>
                  <tr>
                    <th>Jobs Run</th>
                    <th>Successful</th>
                    <th>Failed</th>
                    <th>Canceled</th>
                    <th>Scheduled</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>{this.props.jobsRun}</td>
                    <td>{this.props.jobsSuccessful}</td>
                    <td>{this.props.jobsFailed}</td>
                    <td>{this.props.jobsCanceled}</td>
                    <td>{this.props.jobsScheduled}</td>
                  </tr>
                </tbody>
              </Table>
            </div>
          </div>
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
