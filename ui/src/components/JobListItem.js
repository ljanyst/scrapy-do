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
import Accordion from 'react-bootstrap/Accordion';
import moment from 'moment-timezone';
import hljs from 'highlight.js';
import { LazyLog } from 'react-lazylog';
import { useAccordionToggle } from 'react-bootstrap/AccordionToggle';

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
// Toggle
//------------------------------------------------------------------------------
function Toggle({ text, eventKey }) {
  const onClick = useAccordionToggle(
    eventKey,
    (event) => {
      event.preventDefault();
    });
  return (
    <a href='foo' onClick={onClick}>
      {text}
    </a>
  );
}

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
    // Cancellation button
    //--------------------------------------------------------------------------
    let cancelButton = (
      <div className='item-panel-button'>
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
    let outCollapse = null;
    let outToggle = null;
    let outAccordionKey = `out-${job.identifier}`;
    let errCollapse = null;
    let errToggle = null;
    let errAccordionKey = `err-${job.identifier}`;

    let follow = false;
    if (job.status !== "RUNNING") {
      follow = true;
    }

    outToggle = (
      <Toggle eventKey={outAccordionKey} text='Out Log' />
    );

    errToggle = (
      <Toggle eventKey={errAccordionKey} text='Err Log' />
    );

    outCollapse = (
        <Accordion.Collapse eventKey={outAccordionKey}>
          <div>
            <div className="accordion-header">Out Log</div>
            <div style={{ height: 500 }}>
              <LazyLog
                follow={follow}
                enableSearch
                url={getLogURL(job.identifier, false)}
                caseInsensitive
              />
            </div>
          </div>
        </Accordion.Collapse>
      );

    errCollapse = (
        <Accordion.Collapse eventKey={errAccordionKey}>
          <div>
            <div className="accordion-header">Err Log</div>
            <div style={{ height: 500 }}>
              <LazyLog
                follow={follow}
                enableSearch
                url={getLogURL(job.identifier, true)}
                caseInsensitive
              />
            </div>
          </div>
        </Accordion.Collapse>
      );

    if(this.props.jobList === 'COMPLETED') {
      cancelButton = null;

      if (!job.outLog) {
        outToggle = null;
        outCollapse = null;
      }

      if (!job.errLog) {
        errToggle = null;
        errCollapse = null;
      }
    }

    if(this.props.jobList === 'ACTIVE' && job.status !== "RUNNING") {
      outToggle = null;
      outCollapse = null;
      errToggle = null;
      errCollapse = null;
    }

    //--------------------------------------------------------------------------
    // Payload
    //--------------------------------------------------------------------------
    let payloadCollapse = null;
    let payloadToggle = null;
    let payloadAccordionKey = `payload-${job.identifier}`;
    let payload = JSON.stringify(JSON.parse(job.payload), null, 4);
    const highlighted = hljs.highlight('json', payload).value;

    if (payload !== '{}') {
      payloadToggle = (
        <Toggle eventKey={payloadAccordionKey} text='Payload' />
      );

      payloadCollapse = (
        <Accordion.Collapse eventKey={payloadAccordionKey}>
          <div>
            <div className="accordion-header">Payload</div>
            <pre className='hljs'>
              <code dangerouslySetInnerHTML={{__html: highlighted}} />
            </pre>
          </div>
        </Accordion.Collapse>
      );
    }

    const secondaryPanel = (
      <div className='item-panel' title={dateTime}>
        {outToggle}
        {outToggle && (errToggle || payloadToggle) ? ' | ' : ''}
        {errToggle}
        {errToggle && payloadToggle ? ' | ' : ''}
        {payloadToggle}
        {cancelButton}
      </div>
    );

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
        <Accordion>
        <div className='list-group-item-body'>
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
        </div>
        {payloadCollapse}
        {outCollapse}
        {errCollapse}
        </Accordion>
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
