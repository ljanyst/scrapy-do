//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 29.01.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component } from 'react';

import { FaChartLine, FaBlender, FaBolt, FaRegCheckSquare } from 'react-icons/fa';
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/Navbar';
import { LinkContainer } from 'react-router-bootstrap';

//------------------------------------------------------------------------------
// The navigation bar
//------------------------------------------------------------------------------
class ScrapyDoNav extends Component {

  //----------------------------------------------------------------------------
  // Render the component
  //----------------------------------------------------------------------------
  render() {
    return (
      <Navbar bg='dark' variant='dark' collapseOnSelect expand='md'>
        <LinkContainer to="/">
          <Navbar.Brand>
            Scrapy Do
          </Navbar.Brand>
        </LinkContainer>
        <Navbar.Toggle aria-controls="navbar" />
        <Navbar.Collapse id="navbar">
          <Nav className="mr-auto" />
          <Nav>
            <LinkContainer to="/dashboard">
              <Nav.Link><FaChartLine /> Dashboard</Nav.Link>
            </LinkContainer>
            <LinkContainer to="/project-list">
              <Nav.Link><FaBlender /> Projects</Nav.Link>
            </LinkContainer>
            <LinkContainer to="/job-list/active">
              <Nav.Link><FaBolt /> Active Jobs</Nav.Link>
            </LinkContainer>
            <LinkContainer to="/job-list/completed">
              <Nav.Link><FaRegCheckSquare /> Completed Jobs</Nav.Link>
            </LinkContainer>
          </Nav>
        </Navbar.Collapse>
      </Navbar>
    );
  }
}

export default ScrapyDoNav;
