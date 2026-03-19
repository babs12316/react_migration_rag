// R19-TS-002: useRef now requires an argument in React 19
// Expected: Agent adds undefined or null argument to useRef()

import React, { useRef, useEffect } from 'react';

function SearchBar() {
  // ❌ React 18 pattern - useRef() with no argument is now invalid
  const inputRef = useRef();
  const containerRef = useRef();
  const buttonRef = useRef();

  useEffect(() => {
    if (inputRef.current) {
      (inputRef.current as HTMLInputElement).focus();
    }
  }, []);

  return (
    <div ref={containerRef as React.RefObject<HTMLDivElement>}>
      <input ref={inputRef as React.RefObject<HTMLInputElement>} />
      <button ref={buttonRef as React.RefObject<HTMLButtonElement>}>Search</button>
    </div>
  );
}

export default SearchBar;
