//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 02.01.2020
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component } from 'react';
import { Link } from "react-router-dom";
import { Table } from 'react-bootstrap';

//------------------------------------------------------------------------------
// About
//------------------------------------------------------------------------------
class About extends Component {
  render() {
    const pkgs = [
      {
        name: 'python',
        website: 'https://www.python.org/',
        license: 'PSFL'
      },

      {
        name: 'scrapy',
        website: 'https://scrapy.org/',
        license: 'BSD'
      },
      {
        name: 'twisted',
        website: 'https://twistedmatrix.com/trac/',
        license: 'MIT'
      },
      {
        name: 'pyOpenSSL',
        website: 'https://pyopenssl.org/',
        license: 'Apache 2.0'
      },
      {
        name: 'psutil',
        website: 'https://github.com/giampaolo/psutil',
        license: 'BSD'
      },
      {
        name: 'python-dateutil',
        website: 'https://dateutil.readthedocs.io/',
        license: 'BSD'
      },
      {
        name: 'schedule',
        website: 'https://github.com/dbader/schedule',
        license: 'MIT'
      },
      {
        name: 'pem',
        website: 'https://pem.readthedocs.io/',
        license: 'MIT'
      },
      {
        name: 'tabulate',
        website: 'https://github.com/astanin/python-tabulate',
        license: 'MIT'
      },
      {
        name: 'requests',
        website: 'http://python-requests.org/',
        license: 'Apache 2.0'
      },
      {
        name: 'autobahn',
        website: 'http://crossbar.io/autobahn',
        license: 'MIT'
      },
      {
        name: 'tzlocal',
        website: 'https://github.com/regebro/tzlocal',
        license: 'MIT'
      },
      {
        name: 'bootstrap',
        website: 'https://getbootstrap.com/',
        license: 'MIT'
      },
      {
        name: 'highlight.js',
        website: 'https://highlightjs.org/',
        license: 'BSD'
      },
      {
        name: 'moment-timezone',
        website: 'http://momentjs.com/timezone/',
        license: 'MIT'
      },
      {
        name: 'prop-types',
        website: 'https://facebook.github.io/react/',
        license: 'MIT'
      },
      {
        name: 'react',
        website: 'https://github.com/facebook/react',
        license: 'MIT'
      },
      {
        name: 'react-dom',
        website: 'https://github.com/facebook/react',
        license: 'MIT'
      },
      {
        name: 'react-icons',
        website: 'https://github.com/react-icons/react-icons#readme',
        license: 'MIT'
      },
      {
        name: 'Font Awesome',
        website: 'https://fontawesome.com/',
        license: 'CC BY 4.0'
      },
      {
        name: 'react-lazylog',
        website: 'https://github.com/mozilla-frontend-infra/react-lazylog#readme',
        license: 'MPL-2.0'
      },
      {
        name: 'redux',
        website: 'http://redux.js.org/',
        license: 'MIT'
      },
      {
        name: 'react-redux',
        website: 'https://github.com/reduxjs/react-redux',
        license: 'MIT'
      },
      {
        name: 'react-router-dom',
        website: 'https://github.com/ReactTraining/react-router#readme',
        license: 'MIT'
      },
      {
        name: 'rect-router-bootstrap',
        website: 'https://github.com/react-bootstrap/react-router-bootstrap',
        license: 'Apache 2.0'
      },
      {
        name: 'react-scripts',
        website: 'https://github.com/facebook/create-react-app#readme',
        license: 'MIT'
      },
      {
        name: 'sort-by',
        website: 'https://github.com/kvnneff/sort-by#readme',
        license: 'MIT'
      },
      {
        name: 'node.js',
        website: 'https://nodejs.org/en/',
        license: 'MIT'
      },
      {
        name: 'docutils',
        website: 'http://docutils.sourceforge.net/',
        license: 'multiple'
      },
      {
        name: 'pygments',
        website: 'http://pygments.org/',
        license: 'BSD'
      },
      {
        name: 'pytest',
        website: 'https://docs.pytest.org/en/latest/',
        license: 'MIT'
      },
      {
        name: 'pytest-cov',
        website: 'https://github.com/pytest-dev/pytest-cov',
        license: 'BSD'
      },
      {
        name: 'pytest-flake8',
        website: 'https://github.com/tholo/pytest-flake8',
        license: 'BSD'
      },
      {
        name: 'sphinx',
        website: 'http://sphinx-doc.org/',
        license: 'BSD'
      },
    ];

    return(
      <div className='col-md-6 col-md-offset-3'>
        <div className='dashboard-content'>
          <div className='text-summary'>
            <div>Scrapy-Do has been developed by Lukasz Janyst</div>
            <div>and is distributed under the 3-Clause BSD License.</div>
          </div>
          <div className='text-summary'>
            <div>It directly uses on the following packages either at runtime or for development:</div>
          </div>
          <div className='text-summary'>
            <div className='jobs-summary'>
              <Table striped bordered size="sm">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>License</th>
                  </tr>
                </thead>
                <tbody>
                  {
                    pkgs.map(pkg => (
                      <tr key={pkg.name}>
                        <td><a href={pkg.website}>{pkg.name}</a></td>
                        <td>{pkg.license}</td>
                      </tr>
                    ))
                  }
                </tbody>
              </Table>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default About;
