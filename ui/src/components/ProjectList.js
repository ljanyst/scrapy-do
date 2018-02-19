//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 30.01.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component } from 'react';
import { connect } from 'react-redux';
import { Panel, Button, Glyphicon } from 'react-bootstrap';
import Dialog from 'react-bootstrap-dialog';

import { BACKEND_OPENED } from '../actions/backend';
import { projectPush } from '../utils/backendActions';

import ProjectListItem from './ProjectListItem';

//------------------------------------------------------------------------------
// Project List
//------------------------------------------------------------------------------
class ProjectList extends Component {
  //----------------------------------------------------------------------------
  // File picker change event
  //----------------------------------------------------------------------------
  fileSelectorChange = (event) => {
    const files = event.target.files;
    if(!files.length)
      return;

    this.archivePromise = new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsBinaryString(files[0]);
      reader.onload = () => resolve(btoa(reader.result));
      reader.onerror = error => reject(error);
    });
  };

  //----------------------------------------------------------------------------
  // Show push dialog
  //----------------------------------------------------------------------------
  showPushDialog = () => {
    const content = (
      <div>
        <label>Choose a project archive:</label>
        <input type='file' id='filePicker' accept='.zip'
               onChange={this.fileSelectorChange}/>
      </div>
    );
    this.dialog.show({
      body: content,
      actions: [
        Dialog.CancelAction(),
        Dialog.Action(
          'Push',
          () => {
            if(!this.archivePromise) {
              setTimeout(() => this.dialog.showAlert('No file selected.'), 250);
              return;
            }
            this.archivePromise
              .then(result => projectPush(result))
              .then(() => { this.archivePromise = null; })
              .catch(error => {
                setTimeout(() => this.dialog.showAlert(error.message), 250);
              });
          },
          'btn-primary'
        )
      ]
    });
  };

  //----------------------------------------------------------------------------
  // Render
  //----------------------------------------------------------------------------
  render() {
    const projectNames = this.props.projects;

    var list = (
      <Panel>
        <div className='list-empty'>No projects.</div>
      </Panel>
    );

    if(projectNames.length)
      list = (
        <div>
          {projectNames.map(project => (
            <ProjectListItem
              key={project}
              projectName={project} />
          ))}
        </div>
      );

    return(
      <div className='col-md-8 col-md-offset-2'>
        <Dialog ref={(el) => { this.dialog = el; }} />
        <h2>Projects</h2>
        <div className='control-button-container'>
          <Button
            bsSize="xsmall"
            disabled={!this.props.connected}
            onClick={this.showPushDialog}
          >
          <Glyphicon glyph='upload'/> Push project
        </Button>
        </div>
        {list}
      </div>
    );
  }
}

//------------------------------------------------------------------------------
// The redux connection
//------------------------------------------------------------------------------
function mapStateToProps(state, ownProps) {
  return {
    projects: Object.keys(state.projects).sort(),
    connected: state.backend.status === BACKEND_OPENED
  };
}

function mapDispatchToProps(dispatch) {
  return {};
}

export default connect(mapStateToProps, mapDispatchToProps)(ProjectList);
