//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 03.02.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { Alert } from 'react-bootstrap';

class Poller extends Component {
  //----------------------------------------------------------------------------
  // Property types
  //----------------------------------------------------------------------------
  static propTypes = {
    interval: PropTypes.number.isRequired,
    promiseFunc: PropTypes.func.isRequired,
    callBackFunc: PropTypes.func.isRequired
  }

  //----------------------------------------------------------------------------
  // State
  //----------------------------------------------------------------------------
  state = {
    countdown: 0,
    status: 'ok',
    nextTry: 1
  }

  //----------------------------------------------------------------------------
  // Tick
  //----------------------------------------------------------------------------
  tick = () => {
    this.props.promiseFunc()
      .then((data) => {
        this.setState({ status: 'ok', nextTry: 1 });
        this.timeout = setTimeout(this.tick, this.props.interval);
        return data;
      })
      .then(this.props.callBackFunc)
      .catch(this.errorHandler);

  };

  //----------------------------------------------------------------------------
  // Error tick
  //----------------------------------------------------------------------------
  errorTick = () => {
    if(this.state.countdown === 0) {
      this.setState({ status: 'retry' });
      this.timeout = setTimeout(this.tick, this.props.interval);
      return;
    }
    this.setState((state) => ({ countdown: state.countdown - 1}));
    this.timeout = setTimeout(this.errorTick, 1000);
  };

  //----------------------------------------------------------------------------
  // Error handler
  //----------------------------------------------------------------------------
  errorHandler = (error) => {
    const nextTry = this.state.nextTry*2;
    const interval = nextTry < 256 ? nextTry : 256;
    this.setState({ status: 'error', nextTry: interval, countdown: interval });
    this.timeout = setTimeout(this.errorTick, 1000);
  }

  //----------------------------------------------------------------------------
  // Retry now
  //----------------------------------------------------------------------------
  retryNow = () => {
    this.setState({ countdown: 0 });
  }

  //----------------------------------------------------------------------------
  // Mount
  //----------------------------------------------------------------------------
  componentDidMount() {
    this.timeout = setTimeout(this.tick, this.props.interval);
  }

  //----------------------------------------------------------------------------
  // Unmount
  //----------------------------------------------------------------------------
  componentWillUnmount() {
    clearTimeout(this.timeout);
  }

  //----------------------------------------------------------------------------
  // Render
  //----------------------------------------------------------------------------
  render() {
    //--------------------------------------------------------------------------
    // We're okay
    //--------------------------------------------------------------------------
    if(this.state.status === 'ok')
      return (<div />);

    //--------------------------------------------------------------------------
    // Retrying
    //--------------------------------------------------------------------------
    if(this.state.status === 'retry')
      return (
        <div className='col-md-4 col-md-offset-4'>
          <Alert bsStyle='danger' onClick={this.retryNow}>
            <div className='alert-content'>
              Retrying...
            </div>
          </Alert>
        </div>
      );

    //--------------------------------------------------------------------------
    // Error
    //--------------------------------------------------------------------------
    return (
      <div className='col-md-4 col-md-offset-4'>
        <Alert bsStyle='danger' type='button' onClick={this.retryNow}>
          <div className='alert-content'>
            Connection problem. Retrying in {this.state.countdown} second.
            Click here to retry now.
          </div>
        </Alert>
      </div>
    );
  }
}

export default Poller;
