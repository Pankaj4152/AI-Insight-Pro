import React from 'react';
import './Hamburger.css';

function Hamburger({ isOpen }) {
  return (
    <>
      <span className="hamburger-bar" />
      <span className="hamburger-bar" />
      <span className="hamburger-bar" />
    </>
  );
}

export default Hamburger;