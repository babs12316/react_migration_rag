import { forwardRef } from 'react';



export const Button = forwardRef((props, ref) => {

return <button ref={ref} {...props}>{props.children}</button>;

});
