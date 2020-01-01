//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 29.01.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React from 'react';
import ReactDOM from 'react-dom';
import 'bootstrap/dist/css/bootstrap.css';
import './bootstrap-layout.css';
import './index.css';
import registerServiceWorker from './registerServiceWorker';
import { BrowserRouter } from 'react-router-dom';
import { createStore, combineReducers } from 'redux';
import { Provider } from 'react-redux';

import { backendReducer } from './reducers/backend';
import { statusReducer } from './reducers/status';
import { projectsReducer } from './reducers/projects';
import { jobsReducer } from './reducers/jobs';
import {
  backendStatusSet, backendCountdownSet,
  BACKEND_CONNECTING, BACKEND_OPENED, BACKEND_CLOSED
} from './actions/backend';
import { backend, Backend } from './utils/Backend';
import { messageStoreEvent } from './utils/backendStoreConnectors';

import ScrapyDoApp from './components/ScrapyDoApp';

//------------------------------------------------------------------------------
// Redux store
//------------------------------------------------------------------------------
export const store = createStore(
  combineReducers({
    backend: backendReducer,
    status: statusReducer,
    projects: projectsReducer,
    jobs: jobsReducer
  }),
  window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__()
);

//------------------------------------------------------------------------------
// Make backend events change the state of the stare
//------------------------------------------------------------------------------
const backendStoreEvent = (event, data) => {
  if(event === Backend.CONNECTING)
    store.dispatch(backendStatusSet(BACKEND_CONNECTING));
  else if(event === Backend.OPENED)
    store.dispatch(backendStatusSet(BACKEND_OPENED));
  else if(event === Backend.CLOSED)
    store.dispatch(backendStatusSet(BACKEND_CLOSED));
  else if(event === Backend.COUNTDOWN)
    store.dispatch(backendCountdownSet(data));
};

backend.addEventListener(backendStoreEvent);
backend.addEventListener(messageStoreEvent);

//------------------------------------------------------------------------------
// The App component
//------------------------------------------------------------------------------
ReactDOM.render(
  <Provider store={store}>
    <BrowserRouter>
      <ScrapyDoApp />
    </BrowserRouter>
  </Provider>,
  document.getElementById('root'));

registerServiceWorker();
