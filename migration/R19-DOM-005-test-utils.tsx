// R19-DOM-005: react-dom/test-utils has been removed
// Expected: Agent replaces act import with react package

import React from 'react';

// ❌ React 18 pattern - react-dom/test-utils is removed
import { act } from 'react-dom/test-utils';

function MyComponent() {
  return <div>Test Component</div>;
}

// Example test usage
async function runTest() {
  await act(async () => {
    // test logic here
  });
}

export default MyComponent;
