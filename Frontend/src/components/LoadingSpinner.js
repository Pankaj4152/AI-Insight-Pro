import React from 'react';

const LoadingSpinner = ({ show = false }) => {
  if (!show) return null;

  return (
    <div className={`loading-overlay ${show ? 'show' : ''}`}>
      <div style={{
        width: '40px',
        height: '40px',
        border: '3px solid hsl(220 13% 91%)',
        borderTop: '3px solid hsl(198 88% 32%)',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite'
      }} />
    </div>
  );
};

export default LoadingSpinner;
