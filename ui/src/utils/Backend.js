//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 30.01.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
// Backend
//------------------------------------------------------------------------------
export class Backend {
  //----------------------------------------------------------------------------
  // Constants
  //----------------------------------------------------------------------------
  static CONNECTING = 0;
  static OPENED = 1;
  static CLOSED = 2;
  static MSG_RECEIVED = 3;
  static COUNTDOWN = 4;

  static REMOVE_LISTENER = 0;

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
    this.countdownTimer = null;
    this.countdown = 0;
    this.nextTry = 2;
    this.eventListeners = new Set();
    this.connect();
  }

  //----------------------------------------------------------------------------
  // Connect
  //----------------------------------------------------------------------------
  connect = () => {
    //--------------------------------------------------------------------------
    // Check and clear the existing state
    //--------------------------------------------------------------------------
    if(this.ws)
      throw Error('Socket not closed');

    if(this.countdownTimer)
      clearInterval(this.countdownTimer);

    //--------------------------------------------------------------------------
    // Attempt the connection
    //--------------------------------------------------------------------------
    this.dispatchEvent(Backend.CONNECTING, null);

    this.ws = new WebSocket(this.wsUrl);

    //--------------------------------------------------------------------------
    // On open
    //--------------------------------------------------------------------------
    this.ws.onopen = () => {
      this.dispatchEvent(Backend.OPENED, null);
      this.nextTry = 2;
    };

    //--------------------------------------------------------------------------
    // On Message
    //--------------------------------------------------------------------------
    this.ws.onmessage = (evt) => {
      const message = JSON.parse(evt.data);
      this.dispatchEvent(Backend.MSG_RECEIVED, message);
    };

    //--------------------------------------------------------------------------
    // On Close
    //--------------------------------------------------------------------------
    this.ws.onclose = () => {
      this.dispatchEvent(Backend.CLOSED, null);

      this.ws = null;
      this.nextTry *= 2;
      if(this.nextTry > 256)
        this.nextTry = 256;
      this.countdown = this.nextTry - 1;

      this.dispatchEvent(Backend.COUNTDOWN, this.countdown + 1);

      const tick = () => {
        this.dispatchEvent(Backend.COUNTDOWN, this.countdown);
        if(this.countdown === 0) {
          this.connect();
          return;
        }
        this.countdown -= 1;
      };
      this.countdownTimer = setInterval(tick, 1000);
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

  //----------------------------------------------------------------------------
  // Dispatch event
  //----------------------------------------------------------------------------
  dispatchEvent = (event, data) => {
    let toRemove = [];
    for(const listener of this.eventListeners) {
      let ret = listener(event, data);
      if(ret === Backend.REMOVE_LISTENER)
        toRemove.push(listener);
    }
    for(const listener of toRemove)
      this.removeEventListener(listener);
  }
};

//------------------------------------------------------------------------------
// The backend
//------------------------------------------------------------------------------
export let backend = new Backend();
