// R19-CTX-001: contextTypes removed
// R19-CTX-002: getChildContext removed
// Expected: Agent migrates to React.createContext()

import React from 'react';
import PropTypes from 'prop-types';

// ❌ React 18 pattern - Legacy Context API is removed
class Parent extends React.Component {
  // ❌ getChildContext is removed
  static childContextTypes = {
    theme: PropTypes.string.isRequired,
  };

  getChildContext() {
    return { theme: 'dark' };
  }

  render() {
    return <Child />;
  }
}

class Child extends React.Component {
  // ❌ contextTypes is removed
  static contextTypes = {
    theme: PropTypes.string.isRequired,
  };

  render() {
    return <div>{(this.context as any).theme}</div>;
  }
}

export { Parent, Child };
