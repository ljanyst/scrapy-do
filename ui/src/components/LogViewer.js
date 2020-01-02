//------------------------------------------------------------------------------
// Author: Lukasz Janyst <lukasz@jany.st>
// Date: 02.01.2020
//
// Licensed under the 3-Clause BSD License, see the LICENSE file for details.
//------------------------------------------------------------------------------

import React, { Component } from 'react';
import { LazyLog } from 'react-lazylog';

//------------------------------------------------------------------------------
// Alert dialog
//------------------------------------------------------------------------------
class LogViewer extends Component {
  //----------------------------------------------------------------------------
  // The state
  //----------------------------------------------------------------------------
  state = {
    mounted: false,
    text: ' '
  }

  //----------------------------------------------------------------------------
  // Mounted
  //----------------------------------------------------------------------------
  componentDidMount() {
    this.mounted = true;
  }

  //----------------------------------------------------------------------------
  // Will unmount
  //----------------------------------------------------------------------------
  componentWillUnmount() {
    this.mounted = false;
  }

  //----------------------------------------------------------------------------
  // Fetch some text
  //----------------------------------------------------------------------------
  fetch = () => {
    fetch(this.props.url)
      .catch(error => {
        if (this.mounted) {
          this.setState({
            text: `Error fetching data from ${this.props.url}: error`
          });
        }
      })
      .then(response => response.body.getReader())
      .then(reader => {
        let result = '';
        return reader.read().then(function processText({ done, value }) {
          if (done) {
            return result;
          }
          result += String.fromCharCode.apply(null, value);
          return reader.read().then(processText);
        });
      })
      .then(result => {
        if (this.mounted) {
          this.setState({text: result});
          if (this.props.follow) {
            setTimeout(this.fetch, 1000);
          }
        }
      });
  }

  //----------------------------------------------------------------------------
  // Render
  //----------------------------------------------------------------------------
  render() {
    return(
      <div style={{ height: 500 }}>
        <LazyLog
          extraLines={1}
          scrollToLine={100000000000000000}
          enableSearch={this.props.enableSearch}
          text={this.state.text}
          caseInsensitive={this.props.caseInsensitive}
        />
      </div>
    );
  }
}

export default LogViewer;
