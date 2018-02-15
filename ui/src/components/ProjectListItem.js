//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 13.02.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component } from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { Button, Glyphicon, Panel } from 'react-bootstrap';

//------------------------------------------------------------------------------
// Project List Item
//------------------------------------------------------------------------------
class ProjectListItem extends Component {
  //----------------------------------------------------------------------------
  // Property types
  //----------------------------------------------------------------------------
  static propTypes = {
    projectName: PropTypes.string.isRequired
  }

  //----------------------------------------------------------------------------
  // Render
  //----------------------------------------------------------------------------
  render() {
    const project = this.props;
    return(
      <Panel>
        <Panel.Heading >
          <div className='list-item'>
            <div className='item-panel'>
              <Button
                bsSize="xsmall"
                onClick={() => {}}>
                <Glyphicon glyph='trash'/> Remove
              </Button>
            </div>
            <strong>{project.name}</strong>
          </div>
        </Panel.Heading>
        <Panel.Body>
          <div className='spider-list'>
            {project.spiders.map(spider => (
              <Button bsSize="xsmall" key={spider}>
                <Glyphicon glyph='flash'/> {spider}
              </Button>
            ))}
          </div>
        </Panel.Body>
      </Panel>
    );
  }
}

//------------------------------------------------------------------------------
// The redux connection
//------------------------------------------------------------------------------
function mapStateToProps(state, ownProps) {
  return {
    ...state.projects[ownProps.projectName]
  };
}

function mapDispatchToProps(dispatch) {
  return {};
}

export default connect(mapStateToProps, mapDispatchToProps)(ProjectListItem);
