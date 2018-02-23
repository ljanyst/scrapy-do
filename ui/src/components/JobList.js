//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 30.01.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component } from 'react';
import { connect } from 'react-redux';
import { Panel, Button, Glyphicon, ListGroup } from 'react-bootstrap';

import { BACKEND_OPENED } from '../actions/backend';
import { capitalizeFirst } from '../utils/helpers';

import JobListItem from './JobListItem';

//------------------------------------------------------------------------------
// Job list
//------------------------------------------------------------------------------
class JobList extends Component {
  //----------------------------------------------------------------------------
  // Render
  //----------------------------------------------------------------------------
  render() {
    const jobIds = this.props.jobs;
    const status = this.props.match.params.status;

    //--------------------------------------------------------------------------
    // Job list
    //--------------------------------------------------------------------------
    let list = (
      <Panel>
        <div className='list-empty'>No jobs.</div>
      </Panel>
    );
    if(jobIds.length) {
      list = (
        <ListGroup>
          {jobIds.map(jobId => (
            <JobListItem
              key={jobId}
              jobId={jobId}
              jobList={status.toUpperCase()}
            />
          ))}
        </ListGroup>
      );
    }

    //--------------------------------------------------------------------------
    // Schedule button
    //--------------------------------------------------------------------------
    let scheduleButton = (
      <div className='control-button-container'>
        <Button
          bsSize="xsmall"
          disabled={!this.props.connected}
          >
          <Glyphicon glyph='calendar'/> Schedule a job
        </Button>
      </div>
    );

    if(status === 'completed')
      scheduleButton = null;

    //--------------------------------------------------------------------------
    // The container
    //--------------------------------------------------------------------------
    return(
      <div className='col-md-8 col-md-offset-2'>
        <h2>{capitalizeFirst(status)} Jobs</h2>
        {scheduleButton}
        {list}
      </div>
    );
  }
}

//------------------------------------------------------------------------------
// The redux connection
//------------------------------------------------------------------------------
function mapStateToProps(state, ownProps) {
  const jobStatus = ownProps.match.params.status.toUpperCase();
  let jobs = [];
  if(jobStatus in state.jobs)
    jobs = Object.keys(state.jobs[jobStatus]).sort();
  return {
    jobs,
    connected: state.backend.status === BACKEND_OPENED
  };
}

function mapDispatchToProps(dispatch) {
  return {};
}

export default connect(mapStateToProps, mapDispatchToProps)(JobList);
