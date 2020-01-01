//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 30.12.2019
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component } from 'react';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';

import { projectPush } from '../utils/backendActions';

import AlertDialog from './AlertDialog';

//------------------------------------------------------------------------------
// Push project
//------------------------------------------------------------------------------
class PushProjectDialog extends Component {
  //----------------------------------------------------------------------------
  // The state
  //----------------------------------------------------------------------------
  state = {
    visible: false,
    pushEnabled: false
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
  show = () => {
    this.setState({ visible: true });
  }

  //----------------------------------------------------------------------------
  // Push the project
  //----------------------------------------------------------------------------
  push = () => {
    if(!this.archivePromise) {
      setTimeout(() => this.alert.show('No file selected.'), 250);
      this.close();
      return;
    }

    this.archivePromise
      .then(result => projectPush(result))
      .then(() => { this.archivePromise = null; })
      .catch(error => {
        setTimeout(() => this.alert.show(error.message), 250);
      });
    this.close();
  }

  //----------------------------------------------------------------------------
  // File picker change event
  //----------------------------------------------------------------------------
  fileSelectorChange = (event) => {
    const files = event.target.files;
    if(!files.length)
      return;

    this.setState({ pushEnabled: true });

    this.archivePromise = new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsBinaryString(files[0]);
      reader.onload = () => resolve(btoa(reader.result));
      reader.onerror = error => reject(error);
    });
  };

  //----------------------------------------------------------------------------
  // Render
  //----------------------------------------------------------------------------
  render() {
    return(
      <div>
        <AlertDialog ref={(el) => { this.alert = el; }} />
        <Modal
          show={this.state.visible}
          aria-labelledby="contained-modal-title-vcenter"
          centered
        >
          <Modal.Body>
            <div className='dialog-content-center'>
              <label>Choose a project archive:</label>
              <input type='file' id='filePicker' accept='.zip'
                     onChange={this.fileSelectorChange}/>
            </div>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={this.close}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={this.push}
              disabled={!this.state.pushEnabled}
            >
              Push
            </Button>
          </Modal.Footer>
        </Modal>
      </div>
    );
  }
}

export default PushProjectDialog;

