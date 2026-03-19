// R19-REF-001: Legacy forwardRef detected
// Expected: Agent removes forwardRef and passes ref as a standard prop

import React, { forwardRef } from 'react';

// ❌ React 18 pattern - should be flagged
const Button = forwardRef((props: { label: string }, ref: React.Ref<HTMLButtonElement>) => {
  return (
    <button ref={ref} {...props}>
      {props.label}
    </button>
  );
});

// ❌ Another forwardRef usage
const Input = forwardRef((props: { placeholder: string }, ref: React.Ref<HTMLInputElement>) => {
  return <input ref={ref} placeholder={props.placeholder} />;
});

export { Button, Input };
