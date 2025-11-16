import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';

const PageTransition = ({ children }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isExiting, setIsExiting] = useState(false);
  const location = useLocation();
  const [displayLocation, setDisplayLocation] = useState(location);

  useEffect(() => {
    if (location !== displayLocation) {
      // Start exit animation
      setIsExiting(true);
      setIsVisible(false);
      
      // After exit animation, change the content and start enter animation
      const exitTimer = setTimeout(() => {
        setDisplayLocation(location);
        setIsExiting(false);
        
        // Small delay to ensure content is ready
        const enterTimer = setTimeout(() => {
          setIsVisible(true);
        }, 50);
        
        return () => clearTimeout(enterTimer);
      }, 200);
      
      return () => clearTimeout(exitTimer);
    }
  }, [location, displayLocation]);

  useEffect(() => {
    // Initial load
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, 100);
    
    return () => clearTimeout(timer);
  }, []);

  const transitionStyles = {
    opacity: isVisible ? 1 : 0,
    transform: `translateY(${isVisible ? 0 : (isExiting ? -10 : 20)}px) scale(${isVisible ? 1 : 0.98})`,
    transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
    willChange: 'opacity, transform',
    filter: isVisible ? 'blur(0px)' : 'blur(1px)',
    minHeight: '100vh'
  };

  return (
    <div style={transitionStyles}>
      {children}
    </div>
  );
};

export default PageTransition;
