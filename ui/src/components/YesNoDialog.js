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
// Remove project
//------------------------------------------------------------------------------
class YesNoDialog extends Component {
  //----------------------------------------------------------------------------
  // The state
  //----------------------------------------------------------------------------
  state = {
    visible: false,
    text: ''
  }

  //----------------------------------------------------------------------------
  // No
  //----------------------------------------------------------------------------
  no = () => {
    this.setState({ visible: false });
    if (this.state.no && this.state.no.fn) {
      this.state.no.fn();
    }
  }

  //----------------------------------------------------------------------------
  // Yes
  //----------------------------------------------------------------------------
  yes = () => {
    if (this.state.yes && this.state.yes.fn) {
      this.state.yes.fn();
    }
    this.setState({ visible: false });
  }

  //----------------------------------------------------------------------------
  // Show the modal
  //----------------------------------------------------------------------------
  show = (text, yes, no) => {
    this.setState({
      visible: true,
      text,
      yes,
      no
    });
  }

  //----------------------------------------------------------------------------
  // Render
  //----------------------------------------------------------------------------
  render() {
    var noVariant = 'secondary';
    var yesVariant = 'primary';
    var noText = 'Cancel';
    var yesText = 'Ok';

    if (this.state.no) {
      if (this.state.no.variant) noVariant = this.state.no.variant;
      if (this.state.no.text) noText = this.state.no.text;
    }

    if (this.state.yes) {
      if (this.state.yes.variant) yesVariant = this.state.yes.variant;
      if (this.state.yes.text) yesText = this.state.yes.text;
    }

    return(
      <div>
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
          </Modal.Body>
          <Modal.Footer>
            <Button
              variant={noVariant}
              onClick={this.no}
            >
              {noText}
            </Button>
            <Button
              variant={yesVariant}
              onClick={this.yes}
            >
              {yesText}
            </Button>
          </Modal.Footer>
        </Modal>
      </div>
    );
  }
}

export default YesNoDialog;
