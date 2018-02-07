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
    for(const listener of this.eventListeners)
      listener(Backend.CONNECTING, null);

    this.ws = new WebSocket(this.wsUrl);

    //--------------------------------------------------------------------------
    // On open
    //--------------------------------------------------------------------------
    this.ws.onopen = () => {
      for(const listener of this.eventListeners)
        listener(Backend.OPENED, null);
      this.nextTry = 2;
    };

    //--------------------------------------------------------------------------
    // On Message
    //--------------------------------------------------------------------------
    this.ws.onmessage = (evt) => {
      const message = JSON.parse(evt.data);
      for(const listener of this.eventListeners)
        listener(Backend.MSG_RECEIVED, message);
    };

    //--------------------------------------------------------------------------
    // On Close
    //--------------------------------------------------------------------------
    this.ws.onclose = () => {
      for(const listener of this.eventListeners)
        listener(Backend.CLOSED, null);

      this.ws = null;
      this.nextTry *= 2;
      if(this.nextTry > 256)
        this.nextTry = 256;
      this.countdown = this.nextTry - 1;

      for(const listener of this.eventListeners)
        listener(Backend.COUNTDOWN, this.countdown + 1);

      const tick = () => {
        for(const listener of this.eventListeners)
          listener(Backend.COUNTDOWN, this.countdown);
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
};

//------------------------------------------------------------------------------
// The backend
//------------------------------------------------------------------------------
export let backend = new Backend();
