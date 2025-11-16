import React, { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import Hamburger from "./Hamburger";
import "../Css/Navbar.css";
import { UserCircle, LogOut } from 'lucide-react';

// Menu items for signed-in users (full access)
const authenticatedMenuItems = [
  { label: "Home", path: "/" },
  { label: "SDE Catalogue", path: "/sde-catalogue" },
  { label: "Model Registry", path: "/model-inventory" },
  { label: "Connect", path: "/connect" },
  { label: "Discover", path: "/discover" },
  { label: "Dashboard", path: "/dashboard" },
  { label: "Risk Assessment", path: "/risk-assessment" },
  { label: "Compliance", path: "/compliance" }, // New "Compliance" menu item
  { label: "Report", path: "/report" },
  { label: "ASK", path: "/ask" },
];

// Menu items for compliance officers (limited access)
const complianceOfficerMenuItems = [
  { label: "Dashboard", path: "/dashboard" },
  { label: "Risk Assessment", path: "/risk-assessment" },
  { label: "Compliance", path: "/compliance" },
  { label: "Report", path: "/report" },
  { label: "ASK", path: "/ask" },
];

// Menu items for non-signed-in users (limited access)
const publicMenuItems = [
  { label: "Home", path: "/" },
  { label: "About", path: "/about" },
  { label: "How to Use", path: "/how-to-use" },
  { label: "Contact", path: "/contact" },
];

function HorizontalMenu({ showAuthButtons }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isMobileView, setIsMobileView] = useState(false);
  const currentUserName = localStorage.getItem('client_name');

  // Get user data to check role
  const userData = JSON.parse(localStorage.getItem('user') || '{}');
  const isComplianceOfficer = userData.role === 'compliance-officer';

  // Determine which menu items to show based on authentication status and role
  const isAuthenticated = !!currentUserName || !!userData.username;
  let menuItems;
  if (isAuthenticated) {
    menuItems = isComplianceOfficer ? complianceOfficerMenuItems : authenticatedMenuItems;
  } else {
    menuItems = publicMenuItems;
  }

  const handleLogout = () => {
    localStorage.removeItem('client_id');
    localStorage.removeItem('client_name');
    localStorage.removeItem('client_email');
    localStorage.removeItem('user');
    localStorage.removeItem('client_id_list');
    localStorage.removeItem('selected_client_id');
    navigate('/signup');
    setIsMobileMenuOpen(false);
  };

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isMobileMenuOpen) {
        setIsMobileMenuOpen(false);
      }
    };

    if (isMobileMenuOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
      // document.body.classList.add('mobile-menu-open');
    } else {
      document.body.style.overflow = 'unset';
      // document.body.classList.remove('mobile-menu-open');
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
      // document.body.classList.remove('mobile-menu-open');
    };
  }, [isMobileMenuOpen]);

  // Handle viewport size changes and ensure proper mobile detection
  useEffect(() => {
    const checkViewport = () => {
      const isMobile = window.innerWidth <= 900;
      setIsMobileView(isMobile);
      // Close mobile menu if switching to desktop view
      if (!isMobile && isMobileMenuOpen) {
        setIsMobileMenuOpen(false);
      }
    };

    // Check immediately and then with a small delay to ensure proper viewport calculation
    checkViewport(); // Immediate check
    const timer = setTimeout(checkViewport, 100); // Delayed check for edge cases
    window.addEventListener('resize', checkViewport);
    
    return () => {
      clearTimeout(timer);
      window.removeEventListener('resize', checkViewport);
    };
  }, [isMobileMenuOpen]);

  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location.pathname]);

  const handleHamburgerClick = (e) => {
    e.stopPropagation();
    setIsMobileMenuOpen(prev => !prev);
  };

  const handleOverlayClick = () => {
    setIsMobileMenuOpen(false);
  };

  return (
    <>
      <button
        className={`hamburger ${isMobileMenuOpen ? 'open' : ''}`}
        onClick={handleHamburgerClick}
        aria-label={isMobileMenuOpen ? 'Close menu' : 'Open menu'}
        aria-expanded={isMobileMenuOpen}
      >
        <Hamburger isOpen={isMobileMenuOpen} />
      </button>
      {isMobileView && (
        <>
          <div
            className={`mobile-overlay ${isMobileMenuOpen ? 'open' : ''}`}
            onClick={handleOverlayClick}
            aria-hidden={!isMobileMenuOpen}
          />
          <nav className={`vertical-menu ${isMobileMenuOpen ? 'open' : ''}`} aria-label="Mobile navigation">
        <div className="vertical-menu-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' ,marginLeft: '3.5rem'}}>
            <img
              src="/aip_logo.jpg"
              alt="AIInsight Logo"
              style={{ height: '24px', width: '24px', objectFit: 'contain',gap: '0.5rem' }}
            />
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '0.1rem' }}>
              <span style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--foreground)', lineHeight: '1' }}>
                AIPlaneTech
              </span>
              <span style={{ fontWeight: 600, fontSize: '0.75rem', color: 'var(--foreground)', lineHeight: '1' }}>
                AI-Insight-Pro
              </span>
            </div>
          </div>
        </div>
        <ul className="vertical-menu-list">
          {menuItems.map((item) => (
            <li key={item.label}>
              <Link
                to={item.path}
                className={`vertical-menu-item${location.pathname === item.path ? " active" : ""}`}
                onClick={() => setIsMobileMenuOpen(false)}
                tabIndex={isMobileMenuOpen ? 0 : -1}
              >
                {item.label}
              </Link>
            </li>
          ))}
          {!isAuthenticated && (
            <li>
              <div className="vertical-menu-item sign-in-prompt" style={{ 
                color: 'var(--muted-foreground)', 
                fontSize: '0.85rem',
                fontStyle: 'italic',
                textAlign: 'center',
                padding: '1rem 0.5rem',
                borderTop: '1px solid var(--border)',
                marginTop: '0.5rem'
              }}>
                Sign in to access all features
              </div>
            </li>
          )}
          {showAuthButtons && (
            <>
              {(currentUserName || userData.username) ? (
                <>
                  <li>
                    <Link
                      to="/profile"
                      className={`vertical-menu-item${location.pathname === '/profile' ? ' active' : ''}`}
                      onClick={() => setIsMobileMenuOpen(false)}
                      tabIndex={isMobileMenuOpen ? 0 : -1}
                    >
                      <UserCircle size={20} style={{ marginRight: '0.5rem' }} />
                      {currentUserName || userData.username}
                    </Link>
                  </li>
                  <li>
                    <button
                      onClick={handleLogout}
                      className="vertical-menu-item vertical-auth-btn"
                      tabIndex={isMobileMenuOpen ? 0 : -1}
                    >
                      <LogOut size= {18} style={{ marginRight: '0.5rem' }} />
                      Logout
                    </button>
                  </li>
                </>
              ) : (
                <>
                  <li>
                    <button
                      onClick={() => {
                        navigate('/login');
                        setIsMobileMenuOpen(false);
                      }}
                      className="vertical-menu-item vertical-auth-btn"
                      tabIndex={isMobileMenuOpen ? 0 : -1}
                      style={{ borderBottom: '1px solid var(--border)' }}
                    >
                      Log In
                    </button>
                  </li>
                  <li>
                    <button
                      onClick={() => {
                        navigate('/signup');
                        setIsMobileMenuOpen(false);
                      }}
                      className="vertical-menu-item vertical-auth-btn"
                      tabIndex={isMobileMenuOpen ? 0 : -1}
                      style={{ 
                        background: 'var(--primary)', 
                        color: 'white',
                        fontWeight: '600'
                      }}
                    >
                      Sign Up
                    </button>
                  </li>
                </>
              )}
            </>
          )}
        </ul>
      </nav>
        </>
      )}
      <ul className="horizontal-menu">
        {menuItems.map((item) => (
          <li key={item.label}>
            <Link
              to={item.path}
              className={`horizontal-menu-item${location.pathname === item.path ? " active" : ""}`}
              tabIndex={0}
            >
              <span>{item.label}</span>
            </Link>
          </li>
        ))}
        {!isAuthenticated && (
          <li>
            <div className="horizontal-menu-item sign-in-indicator" style={{
              color: 'var(--muted-foreground)',
              fontSize: '0.8rem',
              fontStyle: 'italic',
              opacity: 0.7,
              cursor: 'default'
            }}>
              Sign in for more
            </div>
          </li>
        )}
      </ul>
    </>
  );
}

export default HorizontalMenu;