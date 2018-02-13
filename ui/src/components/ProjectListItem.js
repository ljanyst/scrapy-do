//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 13.02.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component } from 'react';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import { ListGroupItem } from 'react-bootstrap';

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
      <ListGroupItem>
        <div>
          <strong>
            {project.name}
          </strong>
          <ul>
            {project.spiders.map(spider => (
              <li key={spider}>{spider}</li>
            ))}
          </ul>
        </div>
      </ListGroupItem>
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
