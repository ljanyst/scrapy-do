//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 03.02.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component } from 'react';
import { connect } from 'react-redux';
import Alert from 'react-bootstrap/Alert';

import { backend } from '../utils/Backend';
import { BACKEND_CONNECTING, BACKEND_OPENED } from '../actions/backend';

//------------------------------------------------------------------------------
// Backend status
//------------------------------------------------------------------------------
class BackendStatus extends Component {
  //----------------------------------------------------------------------------
  // Render
  //----------------------------------------------------------------------------
  render() {
    //--------------------------------------------------------------------------
    // We're okay
    //--------------------------------------------------------------------------
    if(this.props.status === BACKEND_OPENED)
      return (<div />);

    //--------------------------------------------------------------------------
    // Retrying
    //--------------------------------------------------------------------------
    if(this.props.status === BACKEND_CONNECTING)
      return (
        <div className='col-md-4 col-md-offset-4'>
          <Alert variant='primary' onClick={this.retryNow}>
            <div className='alert-content'>
              Connecting...
            </div>
          </Alert>
        </div>
      );

    //--------------------------------------------------------------------------
    // Error
    //--------------------------------------------------------------------------
    return (
      <div className='col-md-4 col-md-offset-4'>
        <Alert variant='primary' type='button'>
          <div className='alert-content'>
            Disconnected. Connecting in
            <strong> {this.props.countdown}</strong>
            {this.props.countdown === 1 ? ' second' : ' seconds'}.
            Click <a className='alert-link' onClick={(evt) => {
                evt.preventDefault();
                backend.connect();
              }} href='#n'>here</a> to
            try now.
          </div>
        </Alert>
      </div>
    );
  }
}

//------------------------------------------------------------------------------
// The redux connection
//------------------------------------------------------------------------------
function mapStateToProps(state, ownProps) {
  return {
    status: state.backend.status,
    countdown: state.backend.countdown
  };
}

function mapDispatchToProps(dispatch) {
  return {};
}

export default connect(mapStateToProps, mapDispatchToProps)(BackendStatus);
