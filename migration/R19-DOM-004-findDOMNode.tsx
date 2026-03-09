// R19-DOM-004: ReactDOM.findDOMNode has been removed
// Expected: Agent replaces with useRef

import React, { useEffect } from 'react';
import { findDOMNode } from 'react-dom';

function AutoFocusInput() {
  useEffect(() => {
    // ❌ React 18 pattern - findDOMNode is removed
    const input = findDOMNode(this as any);
    if (input) {
      (input as HTMLInputElement).select();
    }
  }, []);

  return <input defaultValue="Hello" />;
}

export default AutoFocusInput;
