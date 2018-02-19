//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 30.01.2018
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component } from 'react';
import { connect } from 'react-redux';
import { Panel, Button, Glyphicon } from 'react-bootstrap';

import { BACKEND_OPENED } from '../actions/backend';

import ProjectListItem from './ProjectListItem';

//------------------------------------------------------------------------------
// Project List
//------------------------------------------------------------------------------
class ProjectList extends Component {
  render() {
    const projectNames = this.props.projects;

    var list = (
      <Panel>
        <div className='list-empty'>No projects.</div>
      </Panel>
    );

    if(projectNames.length)
      list = (
        <div>
          {projectNames.map(project => (
            <ProjectListItem
              key={project}
              projectName={project} />
          ))}
        </div>
      );

    return(
      <div className='col-md-8 col-md-offset-2'>
        <h2>Projects</h2>
        <div className='control-button-container'>
          <Button
            bsSize="xsmall"
            disabled={!this.props.connected}
            onClick={() => {
            }}
          >
          <Glyphicon glyph='upload'/> Push project
        </Button>
        </div>
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
    projects: Object.keys(state.projects).sort(),
    connected: state.backend.status === BACKEND_OPENED
  };
}

function mapDispatchToProps(dispatch) {
  return {};
}

export default connect(mapStateToProps, mapDispatchToProps)(ProjectList);
