//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 30.01.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
// Backend URL
//------------------------------------------------------------------------------
const url =
    process.env.NODE_ENV === 'production'
      ? ''
      : 'http://localhost:7654';

//------------------------------------------------------------------------------
// Fetch the response or throw an error if the response is not successful
//------------------------------------------------------------------------------
const responseHandler = (response) => {
  if(!response.ok)
    throw Error(response.error);
  return response.json();
};

//------------------------------------------------------------------------------
// Get service status
//------------------------------------------------------------------------------
export function getStatus() {
  return fetch(`${url}/status.json`)
    .then(responseHandler);
};
