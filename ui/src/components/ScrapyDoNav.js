//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 29.01.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component } from 'react';
import { Navbar, Nav, NavItem, Glyphicon } from 'react-bootstrap';
import { LinkContainer } from 'react-router-bootstrap';
import { Link } from 'react-router-dom';

//------------------------------------------------------------------------------
// The navigation bar
//------------------------------------------------------------------------------
class ScrapyDoNav extends Component {

  //----------------------------------------------------------------------------
  // Render the component
  //----------------------------------------------------------------------------
  render() {
    return (
      <Navbar inverse collapseOnSelect>
        <Navbar.Header>
          <Navbar.Brand>
            <Link to="/">
              Scrapy Do
            </Link>
          </Navbar.Brand>
          <Navbar.Toggle />
        </Navbar.Header>
        <Navbar.Collapse>
          <Nav pullRight>
            <LinkContainer to="/dashboard">
              <NavItem><Glyphicon glyph='dashboard'/> Dashboard</NavItem>
            </LinkContainer>

            <LinkContainer to="/project-list">
              <NavItem><Glyphicon glyph='compressed'/> Projects</NavItem>
            </LinkContainer>
            <LinkContainer to="/job-list/active">
              <NavItem><Glyphicon glyph='flash'/> Active Jobs</NavItem>
            </LinkContainer>
            <LinkContainer to="/job-list/completed">
              <NavItem><Glyphicon glyph='check'/> Completed Jobs</NavItem>
            </LinkContainer>
          </Nav>
          </Navbar.Collapse>
      </Navbar>
    );
  }
}

export default ScrapyDoNav;
