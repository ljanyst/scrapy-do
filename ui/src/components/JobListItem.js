//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 21.02.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component } from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import ListGroup from 'react-bootstrap/ListGroup';
import Button from 'react-bootstrap/Button';
import Badge from 'react-bootstrap/Badge';
import moment from 'moment-timezone';

import { BACKEND_OPENED } from '../actions/backend';
import { capitalizeFirst } from '../utils/helpers';
import { jobCancel } from '../utils/backendActions';

import YesNoDialog from './YesNoDialog';
import AlertDialog from './AlertDialog';

//------------------------------------------------------------------------------
// Convert status to label class
//------------------------------------------------------------------------------
const statusToLabel = (status) => {
  switch(status) {
  case 'SCHEDULED': return 'primary';
  case 'PENDING': return 'warning';
  case 'RUNNING': return 'success';
  case 'CANCELED': return 'warning';
  case 'SUCCESSFUL': return 'success';
  case 'FAILED': return 'danger';
  default: return 'primary';
  }
};

//------------------------------------------------------------------------------
// Get log URL
//------------------------------------------------------------------------------
const getLogURL = (jobID, isError) => {
  const logType = isError ? 'err' : 'out';
  return `/get-log/data/${jobID}.${logType}`;
};

//------------------------------------------------------------------------------
// Job List Item
//------------------------------------------------------------------------------
class JobListItem extends Component {
  //----------------------------------------------------------------------------
  // Property types
  //----------------------------------------------------------------------------
  static propTypes = {
    jobId: PropTypes.string.isRequired,
    jobList: PropTypes.string.isRequired
  }

  //----------------------------------------------------------------------------
  // Show cancel dialog
  //----------------------------------------------------------------------------
  showCancelDialog = () => {
    const job = this.props;
    const cancelJob = () => {
      jobCancel(job.identifier)
        .catch((error) => {
          setTimeout(() => this.alertDialog.show(error.message), 250);
        });
    };

    const yes = {
      variant: 'danger',
      text: 'Yes',
      fn: cancelJob
    };
    const no = {
      text: 'No'
    };

    const msg = `Are you sure you want to cancel the job?`;
    this.cancelDialog.show(msg, yes, no);
  };

  //----------------------------------------------------------------------------
  // Render the component
  //----------------------------------------------------------------------------
  render() {
    const job = this.props;
    const timestamp = moment.unix(job.timestamp);
    const dateTime = timestamp.tz(this.props.timezone)
          .format('YYYY-MM-DD HH:mm:ss');

    //--------------------------------------------------------------------------
    // Logs and cancellation button
    //--------------------------------------------------------------------------
    let runningLogs = '';
    if(job.status === "RUNNING") {
      runningLogs = (
        <div className='item-log'>
          <a href={getLogURL(job.identifier, false)}>Out Log</a>
          &nbsp;|&nbsp;
          <a href={getLogURL(job.identifier, true)}>Error Log</a>
        </div>
      );
    }

    let secondaryPanel = (
      <div className='item-panel' title={dateTime}>
        {runningLogs}
        <Button
          variant="outline-secondary"
          size="sm"
          disabled={!this.props.connected}
          onClick={this.showCancelDialog}
        >
          Cancel
        </Button>

      </div>
    );

    //--------------------------------------------------------------------------
    // Logs
    //--------------------------------------------------------------------------
    if(this.props.jobList === 'COMPLETED') {
      secondaryPanel = (
        <div className='item-panel'>
          {
            job.outLog
              ? (<a href={getLogURL(job.identifier, false)}>Out Log</a>)
              : ''}
          {job.outLog && job.errLog ? ' | ' : ''}
          {
            job.errLog
              ? (<a href={getLogURL(job.identifier, true)}>Error Log</a>)
              : ''
          }
          </div>
      );
    }

    //--------------------------------------------------------------------------
    // Render the whole thing
    //--------------------------------------------------------------------------
    var description = '';
    if (job.description !== '') {
      description = `[${job.description}]`;
    }

    return (
      <ListGroup.Item>
        <YesNoDialog ref={(el) => { this.cancelDialog = el; }} />
        <AlertDialog ref={(el) => { this.alertDialog = el; }} />
        <div className='list-item'>
          <div className='item-panel' title={dateTime}>
            {timestamp.fromNow()}
          </div>
          <Badge variant={statusToLabel(job.status)}>
            {job.status}
          </Badge>
          <strong> {job.spider} {description}</strong> ({job.project})
        </div>
        <div className='list-item-secondary'>
          {secondaryPanel}
          Scheduled by {capitalizeFirst(job.actor)} to run {job.schedule}.
        </div>
      </ListGroup.Item>
    );
  }
}

//------------------------------------------------------------------------------
// The redux connection
//------------------------------------------------------------------------------
function mapStateToProps(state, ownProps) {
  return {
    ...state.jobs[ownProps.jobList][ownProps.jobId],
    timezone: state.status.timezone,
    connected: state.backend.status === BACKEND_OPENED
  };
}

function mapDispatchToProps(dispatch) {
  return {};
}

export default connect(mapStateToProps, mapDispatchToProps)(JobListItem);
