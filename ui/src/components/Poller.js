//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 03.02.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component } from 'react';
import PropTypes from 'prop-types';

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
    console.log('tick');
    this.props.promiseFunc()
      .then((data) => {
        this.setState({ status: 'ok', nextTry: 1 });
        console.log('success');
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
    console.log('error tick');
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
    console.log('error', this.state.nextTry);
    const nextTry = this.state.nextTry*2;
    const interval = nextTry < 256 ? nextTry : 256;
    this.setState({ status: 'error', nextTry: interval, countdown: interval });
    this.timeout = setTimeout(this.errorTick, 1000);
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
    return (
      <div>
        <p>Status: {this.state.status} </p>
        <p>Countdown:  {this.state.countdown}</p>
      </div>
    );
  }
}

export default Poller;
