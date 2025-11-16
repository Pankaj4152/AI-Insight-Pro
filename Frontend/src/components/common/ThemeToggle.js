import React, { useEffect, useState } from 'react';
import '../../Css/ThemeToggle.css'; // Import the CSS for ThemeToggle
import { SunIcon, MoonIcon } from 'lucide-react'; // Import icons

function ThemeToggle() {
  // Initialize theme from localStorage or default to 'dark'
  const [theme, setTheme] = useState(() => {
    const savedTheme = localStorage.getItem('theme');
    return savedTheme || 'dark'; // Default to dark theme
  });

  // Apply theme by setting data-theme attribute on body
  useEffect(() => {
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    // Add temporary focus class for animation
    const toggleContainer = document.querySelector('.theme-toggle-container');
    if (toggleContainer) {
      toggleContainer.classList.add('focus-visible');
      setTimeout(() => {
        toggleContainer.classList.remove('focus-visible');
      }, 1000);
    }
    setTheme(prevTheme => (prevTheme === 'light' ? 'dark' : 'light'));
  };

  return (
    <div className="theme-toggle-container" onClick={toggleTheme} role="button" tabIndex={0}>
      <div className="theme-icons">
        {/* Sun icon for light theme */}
        <span className={`theme-icon sun ${theme === 'light' ? 'active' : ''}`}>
          <SunIcon className="toggleIcon" />
        </span>
        {/* Moon icon for dark theme */}
        <span className={`theme-icon moon ${theme === 'dark' ? 'active' : ''}`}>
          <MoonIcon className="toggleIcon" />
        </span>
      </div>
    </div>
  );
}

export default ThemeToggle;