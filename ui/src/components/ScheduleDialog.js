//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 25.02.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component } from 'react';
import { connect } from 'react-redux';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';

import Form from 'react-bootstrap/Form';

import { jobSchedule } from '../utils/backendActions';
import { scheduleValid } from '../utils/helpers';

import AlertDialog from './AlertDialog';

//------------------------------------------------------------------------------
// Schedule Dialog
//------------------------------------------------------------------------------
class ScheduleDialog extends Component {
  //----------------------------------------------------------------------------
  // The state
  //----------------------------------------------------------------------------
  state = {
    visible: false,
    project: '__select',
    spider: '__select',
    schedule: 'now',
    projectsDisabled: false,
    spidersDisabled: true,
    scheduleDisabled: true,
    submitDisabled: true,
    scheduleValidated: true
  }

  //----------------------------------------------------------------------------
  // Set up the dialog controller
  //----------------------------------------------------------------------------
  componentDidMount() {
    this.props.provideController({
      show: this.show
    });
  }

  componentWillUnmount() {
    this.props.provideController(null);
  }

  //----------------------------------------------------------------------------
  // Close the modal
  //----------------------------------------------------------------------------
  close = () => {
    this.setState({ visible: false });
  }

  //----------------------------------------------------------------------------
  // Show the modal
  //----------------------------------------------------------------------------
  show = (project, spider) => {
    this.setState({
      visible: true,
      project: project ? project : '__select',
      spider: spider ? spider : '__select',
      schedule: 'now',
      projectsDisabled: project ? true : false,
      spidersDisabled: true,
      scheduleDisabled: project && spider ? false : true,
      submitDisabled: project && spider ? false : true,
      validated: true
    });
  }

  //----------------------------------------------------------------------------
  // Show the dialog for a given spider
  //----------------------------------------------------------------------------
  showForSpider = (project, spider) => {
    this.setState({
      show: true,
      project,
      spider,
      projectsDisabled: true,
      scheduleDisabled: false,
      submitDisabled: false
    });
  }

  //----------------------------------------------------------------------------
  // Schedule the job
  //----------------------------------------------------------------------------
  schedule = () => {
    jobSchedule(this.state.project, this.state.spider, this.state.schedule)
      .catch(error => {
        setTimeout(() => this.alert.show(error.message), 250);
      });
    this.close();
  }

  //----------------------------------------------------------------------------
  // On project change
  //----------------------------------------------------------------------------
  onProjectChange = (event) => {
    if(event.target.value === '__select')
      this.setState({
        spidersDisabled: true,
        scheduleDisabled: true,
        submitDisabled: true,
        project: event.target.value
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
        submitDisabled: true,
        spider: event.target.value
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
    const scheduleValidated = scheduleValid(event.target.value);
    this.setState({
      schedule: event.target.value,
      scheduleValidated: scheduleValidated,
      submitDisabled: !scheduleValidated
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
      <Form.Group controlId="projectSelect">
        <Form.Label>Project</Form.Label>
        <Form.Control
          as='select'
          placeholder='__select'
          disabled={this.state.projectsDisabled}
          onChange={this.onProjectChange}
          value={this.state.project}
        >
          <option value='__select'>Select Project</option>
          {this.props.__projects.map(project => (
            <option key={project} value={project}>
              {project}
            </option>
          ))}
        </Form.Control>
      </Form.Group>
    );

    //--------------------------------------------------------------------------
    // Spider selector
    //--------------------------------------------------------------------------
    let spiders = [];
    if(this.state.project !== '__select' && this.state.project in this.props) {
      spiders = this.props[this.state.project].spiders;
    }

    const spiderSelector = (
      <Form.Group controlId='spiderSelect'>
        <Form.Label>Spider</Form.Label>
        <Form.Control
          as='select'
          placeholder='__select'
          disabled={this.state.spidersDisabled}
          onChange={this.onSpiderChange}
          value={this.state.spider}
        >
          <option value='__select'>Select Spider</option>
          {spiders.map(spider => (
            <option key={spider} value={spider}>
              {spider}
            </option>
          ))}
        </Form.Control>
      </Form.Group>
    );

    //--------------------------------------------------------------------------
    // Schedule input
    //--------------------------------------------------------------------------
    const specDocLink = 'https://scrapy-do.readthedocs.io/en/latest/basic-concepts.html#scheduling-specs';
    const scheduleInput = (
      <Form.Group
        controlId='scheduleInput'
      >
        <Form.Label>Schedule</Form.Label>
        <Form.Control
          type='text'
          disabled={this.state.scheduleDisabled}
          value={this.state.schedule}
          onChange={this.onScheduleChange}
          isInvalid={!this.state.scheduleValidated}
          isValid={this.state.scheduleValidated}
        />

        <Form.Control.Feedback type="valid">
          See the <a href={specDocLink}>docs</a> on scheduling specs.
        </Form.Control.Feedback>

        <Form.Control.Feedback type="invalid">
          See the <a href={specDocLink}>docs</a> on scheduling specs.
        </Form.Control.Feedback>

      </Form.Group>
    );

    //--------------------------------------------------------------------------
    // The whole thing
    //--------------------------------------------------------------------------
    return (
      <div>
        <AlertDialog ref={(el) => { this.alert = el; }} />
        <Modal
          show={this.state.visible}
          aria-labelledby="contained-modal-title-vcenter"
          centered
        >
          <Modal.Body>
            <div className='dialog-content-left'>
              {projectSelector}
              {spiderSelector}
              {scheduleInput}
            </div>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={this.close}>
              Cancel
            </Button>
            <Button
              variant="success"
              onClick={this.schedule}
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
