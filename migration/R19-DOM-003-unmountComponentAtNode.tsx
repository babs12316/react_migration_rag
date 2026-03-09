// R19-DOM-003: unmountComponentAtNode has been removed
// Expected: Agent replaces with root.unmount()

import React from 'react';
import ReactDOM from 'react-dom';

function App() {
  return <h1>Hello</h1>;
}

const container = document.getElementById('root');

// ❌ React 18 pattern - unmountComponentAtNode is removed
ReactDOM.unmountComponentAtNode(container!);
