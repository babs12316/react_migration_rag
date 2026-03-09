// R19-REF-003: MutableRefObject is deprecated
// Expected: Agent replaces MutableRefObject with RefObject

import React, { useRef } from 'react';

interface Props {
  initialCount: number;
}

function Counter({ initialCount }: Props) {
  // ❌ React 18 pattern - MutableRefObject is deprecated
  const countRef = useRef<number>(initialCount) as React.MutableRefObject<number>;

  // ❌ Another MutableRefObject usage
  const inputRef: React.MutableRefObject<HTMLInputElement | null> = useRef(null);

  return (
    <div>
      <input ref={inputRef} />
      <span>{countRef.current}</span>
    </div>
  );
}

export default Counter;
