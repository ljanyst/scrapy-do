//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 30.01.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component } from 'react';
import { connect } from 'react-redux';
import { ListGroup, Panel } from 'react-bootstrap';

import ProjectListItem from './ProjectListItem';

//------------------------------------------------------------------------------
// Project List
//------------------------------------------------------------------------------
class ProjectList extends Component {
  render() {
    const projectNames = Object.keys(this.props.projects);

    var list = (
      <Panel>
        <div className='list-empty'>No projects.</div>
      </Panel>
    );

    if(projectNames.length)
      list = (
        <ListGroup>
          {projectNames.map(project => (
            <ProjectListItem
              key={project}
              projectName={project} />
          ))}
        </ListGroup>
      );

    return(
      <div className='col-md-8 col-md-offset-2'>
        <h2>Projects</h2>
        {list}
      </div>
    );
  }
}

//------------------------------------------------------------------------------
// The redux connection
//------------------------------------------------------------------------------
function mapStateToProps(state, ownProps) {
  return {
    projects: state.projects
  };
}

function mapDispatchToProps(dispatch) {
  return {};
}

export default connect(mapStateToProps, mapDispatchToProps)(ProjectList);
