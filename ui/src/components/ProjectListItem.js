//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 13.02.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component } from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';
import Card from 'react-bootstrap/Card';
import { FaRegTrashAlt, FaBolt } from 'react-icons/fa';

import { BACKEND_OPENED } from '../actions/backend';
import { projectRemove } from '../utils/backendActions';

import ScheduleDialog from './ScheduleDialog';
import YesNoDialog from './YesNoDialog';
import AlertDialog from './AlertDialog';

//------------------------------------------------------------------------------
// Project List Item
//------------------------------------------------------------------------------
class ProjectListItem extends Component {
  //----------------------------------------------------------------------------
  // Property types
  //----------------------------------------------------------------------------
  static propTypes = {
    projectName: PropTypes.string.isRequired
  }

  //----------------------------------------------------------------------------
  // Show the remove dialog
  //----------------------------------------------------------------------------
  showRemoveDialog = () => {
    const project = this.props;
    const removeProject = () => {
      projectRemove(project.name)
        .catch((error) => {
          setTimeout(() => this.alertDialog.show(error.message), 250);
        });
    };

    const yes = {
      variant: 'danger',
      text: 'Remove',
      fn: removeProject
    };

    const msg = `Are you sure you want to remove project "${project.name}"?`;
    this.removeDialog.show(msg, yes);
  }

  //----------------------------------------------------------------------------
  // Render
  //----------------------------------------------------------------------------
  render() {
    const project = this.props;
    return(
      <div className='project-list-item'>
        <YesNoDialog ref={(el) => { this.removeDialog = el; }} />
        <AlertDialog ref={(el) => { this.alertDialog = el; }} />
        <ScheduleDialog
          provideController={ctl => this.scheduleDialogCtl = ctl}
        />
        <Card>
          <Card.Header>
            <div className='list-item'>
              <div className='item-panel'>
                <Button
                  size='sm'
                  variant='secondary'
                  disabled={!this.props.connected}
                  onClick={this.showRemoveDialog}
                >
                  <FaRegTrashAlt /> Remove
                </Button>
              </div>
              <strong>{project.name}</strong>
            </div>
          </Card.Header>
          <Card.Body>
            <div className='spider-list'>
              {project.spiders.map(spider => (
                <Button
                  size='sm'
                  variant='outline-secondary'
                  disabled={!this.props.connected}
                  key={spider}
                  onClick={() => {
                    this.scheduleDialogCtl.show(project.name, spider);
                  }}
                >
                  <FaBolt /> {spider}
                </Button>
              ))}
            </div>
          </Card.Body>
        </Card>
      </div>
    );
  }
}

//------------------------------------------------------------------------------
// The redux connection
//------------------------------------------------------------------------------
function mapStateToProps(state, ownProps) {
  return {
    ...state.projects[ownProps.projectName],
    connected: state.backend.status === BACKEND_OPENED
  };
}

function mapDispatchToProps(dispatch) {
  return {};
}

export default connect(mapStateToProps, mapDispatchToProps)(ProjectListItem);
