//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 30.01.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React from 'react';
import { FaDirections } from 'react-icons/fa';

export default function WrongRoute(props) {
  return (
    <div className='col-md-8 col-md-offset-2'>
      <div style={{textAlign: 'center'}}>
        <div style={{margin: '3em'}}>
          <FaDirections size={300} color='DimGrey'/>
        </div>
        <h3>This is not what you're looking for.</h3>
        </div>
    </div>
  );
}
