// R19-TYPES-002: defaultProps for function components removed
// Expected: Agent replaces with ES6 default parameters

import React from 'react';

interface ButtonProps {
  label?: string;
  color?: string;
  size?: string;
}

// ❌ React 18 pattern - defaultProps is removed for function components
function Button({ label, color, size }: ButtonProps) {
  return (
    <button style={{ color, fontSize: size }}>
      {label}
    </button>
  );
}

Button.defaultProps = {
  label: 'Click me',
  color: 'blue',
  size: '16px',
};

export default Button;
