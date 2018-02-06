//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 30.01.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
// Backend
//------------------------------------------------------------------------------
class Backend {
  //----------------------------------------------------------------------------
  // Constants
  //----------------------------------------------------------------------------
  static OPENED = 0;
  static CLOSED = 1;
  static MSG_RECEIVED = 3;

  //----------------------------------------------------------------------------
  // Constructor
  //----------------------------------------------------------------------------
  constructor() {
    const loc = window.location;
    const wsProtocol = loc.protocol === 'https:' ? 'wss:' : 'ws:';
    this.wsUrl =
      process.env.NODE_ENV === 'production'
        ? `${wsProtocol}//${loc.host}/ws`
        : 'ws://localhost:7654/ws';

    this.ws = null;
    this.eventListeners = new Set();
    this.connect();
  }

  //----------------------------------------------------------------------------
  // Connect
  //----------------------------------------------------------------------------
  connect = () => {
    this.ws = new WebSocket(this.wsUrl);

    this.ws.onopen = () => {
      for(const listener of this.eventListeners)
        listener(Backend.OPENED, null);
    };

    this.ws.onmessage = (evt) => {
      const message = JSON.parse(evt.data);
      for(const listener of this.eventListeners)
        listener(Backend.MSG_RECEIVED, message);
    };

    this.ws.onclose = () => {
      for(const listener of this.eventListeners)
        listener(Backend.CLOSED, null);
    };
  };

  //----------------------------------------------------------------------------
  // Add event listener
  //----------------------------------------------------------------------------
  addEventListener = (listener) => {
    this.eventListeners.add(listener);
  }

  //----------------------------------------------------------------------------
  // Remove an event listener
  //----------------------------------------------------------------------------
  removeEventListener = (listener) => {
    this.eventListeners.delete(listener);
  }
};

//------------------------------------------------------------------------------
// The backend
//------------------------------------------------------------------------------
export let backend = new Backend();
