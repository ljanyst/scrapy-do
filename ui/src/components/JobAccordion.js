//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 01.01.2020
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component, useState } from 'react';
import Accordion from 'react-bootstrap/Accordion';
import { useAccordionToggle } from 'react-bootstrap/AccordionToggle';

//------------------------------------------------------------------------------
// Toggle
//------------------------------------------------------------------------------
function Toggle({ textActive, textInactive, eventKey }) {
  const [active, setActive] = useState(false);
  const onClick = useAccordionToggle(
    eventKey,
    (event) => {
      event.preventDefault();
      setActive(!active);
    });
  return (
    <div className="accordion-header">
      <a href='foo' onClick={onClick}>
        {active ? textActive : textInactive}
      </a>
    </div>
  );
}

//------------------------------------------------------------------------------
// Job accordion
//------------------------------------------------------------------------------
class JobAccordion extends Component {
  //----------------------------------------------------------------------------
  // Render
  //----------------------------------------------------------------------------
  render() {
    return(
      <div>
        <Accordion>
          <Toggle
            eventKey={this.props.eventKey}
            textActive={this.props.textActive}
            textInactive={this.props.textInactive}
          />
          <Accordion.Collapse eventKey={this.props.eventKey}>
            {this.props.children}
          </Accordion.Collapse>
        </Accordion>
      </div>
    );
  }
}

export default JobAccordion;
