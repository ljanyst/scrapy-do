//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 25.02.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component } from 'react';
import { connect } from 'react-redux';
import {
  FormGroup, ControlLabel, FormControl, Modal, Button
} from 'react-bootstrap';

//------------------------------------------------------------------------------
// Validate the schedule
//------------------------------------------------------------------------------
function scheduleValid(schedule) {
  if(schedule.length)
    return true;
  return false;
};

//------------------------------------------------------------------------------
// Default state
//------------------------------------------------------------------------------
const defaultState = {
  show: false,
  spidersDisabled: true,
  scheduleDisabled: true,
  submitDisabled: true,
  project: null,
  spider: null,
  schedule: 'now'
};

//------------------------------------------------------------------------------
// Schedule Dialog
//------------------------------------------------------------------------------
class ScheduleDialog extends Component {
  state = defaultState;

  //----------------------------------------------------------------------------
  // Set up the dialog controller
  //----------------------------------------------------------------------------
  componentDidMount() {
    this.props.provideController({
      show: this.show
    });
  }

  //----------------------------------------------------------------------------
  // Clean up the dialog controller
  //----------------------------------------------------------------------------
  componentWillUnmount() {
    this.props.provideController(null);
  }

  //----------------------------------------------------------------------------
  // Show the dialog
  //----------------------------------------------------------------------------
  show = () => {
    this.setState({show: true});
  }

  //----------------------------------------------------------------------------
  // Hide the dialog
  //----------------------------------------------------------------------------
  hide = () => {
    this.setState(defaultState);
  }

  //----------------------------------------------------------------------------
  // On project change
  //----------------------------------------------------------------------------
  onProjectChange = (event) => {
    if(event.target.value === '__select')
      this.setState({
        spidersDisabled: true,
        scheduleDisabled: true,
        submitDisabled: true
      });
    else
      this.setState({
        spidersDisabled: false,
        project: event.target.value
      });
  }

  //----------------------------------------------------------------------------
  // On spider change
  //----------------------------------------------------------------------------
  onSpiderChange = (event) => {
    if(event.target.value === '__select')
      this.setState({
        scheduleDisabled: true,
        submitDisabled: true
      });
    else
      this.setState({
          scheduleDisabled: false,
          submitDisabled: !scheduleValid(this.state.schedule),
          spider: event.target.value
      });
  }

  //----------------------------------------------------------------------------
  // On schedule change
  //----------------------------------------------------------------------------
  onScheduleChange = (event) => {
    this.setState({
      schedule: event.target.value,
      submitDisabled: !scheduleValid(event.target.value)
    });
  };

  //----------------------------------------------------------------------------
  // Render the dialog
  //----------------------------------------------------------------------------
  render() {
    //--------------------------------------------------------------------------
    // Project selector
    //--------------------------------------------------------------------------
    const projectSelector = (
      <FormGroup controlId='projectSelect'>
        <ControlLabel>Project</ControlLabel>
        <FormControl componentClass='select' placeholder='__select'
                     onChange={this.onProjectChange}
        >
          <option value='__select'>Select Project</option>
          {this.props.__projects.map(project => (
            <option key={project} value={project}>{project}</option>
          ))}
        </FormControl>
      </FormGroup>
    );

    //--------------------------------------------------------------------------
    // Spider selector
    //--------------------------------------------------------------------------
    let spiders = [];
    if(!this.state.spidersDisabled && this.state.project in this.props)
      spiders = this.props[this.state.project].spiders;

    const spiderSelector = (
      <FormGroup controlId='spiderSelect'>
        <ControlLabel>Spider</ControlLabel>
        <FormControl componentClass='select' placeholder='__select'
                     disabled={this.state.spidersDisabled}
                     onChange={this.onSpiderChange}
        >
          <option value='__select'>Select Spider</option>
          {spiders.map(spider => (
            <option key={spider} value={spider}>{spider}</option>
          ))}
        </FormControl>
      </FormGroup>
    );

    //--------------------------------------------------------------------------
    // Schedule input
    //--------------------------------------------------------------------------
    const scheduleInput = (
      <FormGroup controlId='scheduleInput'
                 validationState={scheduleValid(this.state.schedule) ? 'success' : 'error'}
      >
        <ControlLabel>Schedule</ControlLabel>
        <FormControl type='text' disabled={this.state.scheduleDisabled}
                     value={this.state.schedule}
                     onChange={this.onScheduleChange} />
        <FormControl.Feedback />
      </FormGroup>
    );

    //--------------------------------------------------------------------------
    // The whole thing
    //--------------------------------------------------------------------------
    return (
      <div>
        <Modal show={this.state.show} onHide={this.handleClose} bsSize='small'>
          <Modal.Body>
            {projectSelector}
            {spiderSelector}
            {scheduleInput}
          </Modal.Body>
          <Modal.Footer>
            <Button
              onClick={this.hide}
              bsSize='small'
            >
              Cancel
            </Button>
            <Button
              onClick={this.hide}
              bsStyle='primary'
              bsSize='small'
              disabled={this.state.submitDisabled}
            >
              Schedule
            </Button>
          </Modal.Footer>
        </Modal>
      </div>
    );
  }
}

//------------------------------------------------------------------------------
// The redux connection
//------------------------------------------------------------------------------
function mapStateToProps(state, ownProps) {
  return {
    __projects: Object.keys(state.projects).sort(),
    ...state.projects
  };
}

function mapDispatchToProps(dispatch) {
  return {};
}

export default connect(mapStateToProps, mapDispatchToProps)(ScheduleDialog);
