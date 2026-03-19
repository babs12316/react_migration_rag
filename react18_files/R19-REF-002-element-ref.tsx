// R19-REF-002: Accessing element.ref is deprecated
// Expected: Agent replaces element.ref with element.props.ref

import React from 'react';

function ParentComponent() {
  const child = <input />;

  // ❌ React 18 pattern - element.ref is deprecated
  const refValue = child.ref;

  // ❌ Another element.ref access
  function getRef(element: React.ReactElement) {
    return element.ref;
  }

  return <div>{child}</div>;
}

export default ParentComponent;
