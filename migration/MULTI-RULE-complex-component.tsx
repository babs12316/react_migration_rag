// MULTI-RULE TEST: Triggers multiple React 19 issues at once
// Rules triggered: R19-REF-001, R19-TYPES-001, R19-TYPES-002, R19-DOM-001

import React, { forwardRef } from 'react';
import PropTypes from 'prop-types';
import { render } from 'react-dom';

// ❌ R19-TYPES-001: propTypes used
// ❌ R19-TYPES-002: defaultProps used
// ❌ R19-REF-001: forwardRef used
const LegacyCard = forwardRef((
  props: { title?: string; description?: string; color?: string },
  ref: React.Ref<HTMLDivElement>
) => {
  return (
    <div ref={ref} style={{ borderColor: props.color }}>
      <h2>{props.title}</h2>
      <p>{props.description}</p>
    </div>
  );
});

LegacyCard.propTypes = {
  title: PropTypes.string,
  description: PropTypes.string,
  color: PropTypes.string,
};

LegacyCard.defaultProps = {
  title: 'Default Title',
  description: 'Default Description',
  color: 'blue',
};

// ❌ R19-DOM-001: ReactDOM.render used
render(<LegacyCard />, document.getElementById('root'));

export default LegacyCard;
