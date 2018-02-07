//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 29.01.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React from 'react';
import ReactDOM from 'react-dom';
import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap/dist/css/bootstrap-theme.css';
import './index.css';
import registerServiceWorker from './registerServiceWorker';
import { BrowserRouter } from 'react-router-dom';
import { createStore, combineReducers } from 'redux';
import { Provider } from 'react-redux';

import { backendReducer } from './reducers';

import ScrapyDoApp from './components/ScrapyDoApp';

//------------------------------------------------------------------------------
// Redux store
//------------------------------------------------------------------------------
const store = createStore(
  combineReducers({
    backend: backendReducer
  }),
  window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__()
);

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
