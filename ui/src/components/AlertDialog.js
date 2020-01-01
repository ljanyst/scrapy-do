//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 30.12.2019
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component } from 'react';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';

//------------------------------------------------------------------------------
// Alert dialog
//------------------------------------------------------------------------------
class AlertDialog extends Component {
  //----------------------------------------------------------------------------
  // The state
  //----------------------------------------------------------------------------
  state = {
    visible: false,
    text: ''
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
  show = (text) => {
    this.setState({ visible: true, text: text });
  }

  //----------------------------------------------------------------------------
  // Render
  //----------------------------------------------------------------------------
  render() {
    return(
      <Modal
        show={this.state.visible}
        aria-labelledby="contained-modal-title-vcenter"
        centered
        size='sm'
      >
        <Modal.Body>
          <div className='dialog-content-center'>
            {this.state.text}
          </div>
          <hr/>
          <div className='alert-content'>
            <Button variant="secondary" onClick={this.close}>
              OK
            </Button>
          </div>
        </Modal.Body>
      </Modal>
    );
  }
}

export default AlertDialog;

