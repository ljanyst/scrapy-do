//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 29.01.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React from 'react';
import ReactDOM from 'react-dom';
import 'bootstrap/dist/css/bootstrap.css';
import './index.css';
import ScrapyDoApp from './components/ScrapyDoApp';
import registerServiceWorker from './registerServiceWorker';

ReactDOM.render(<ScrapyDoApp />, document.getElementById('root'));
registerServiceWorker();
