import React, { useState, useEffect } from 'react';

import HorizontalMenu from './Navbar';
import RoleSelectionModal from './RoleSelectionModal';
import '../Css/App.css';
import '../Css/Header.css';
import { Link, useNavigate } from 'react-router-dom';
import { UserCircle, LogOut, ChevronDown } from 'lucide-react';
import { clearRiskAssessmentClientIdCache } from '../utils/clientUtils';



const Header = () => {
  const navigate = useNavigate();
  const currentUserName = localStorage.getItem('client_name');
  const [isScrolled, setIsScrolled] = useState(false);
  const [showClientDropdown, setShowClientDropdown] = useState(false);

  const [showRoleSelection, setShowRoleSelection] = useState(false);
  const [modalMode, setModalMode] = useState('signup'); // 'signup' or 'login'

  // Get user data and client list
  const userData = JSON.parse(localStorage.getItem('user') || '{}');
  const clientIdList = JSON.parse(localStorage.getItem('client_id_list') || '{}');
  const isComplianceOfficer = userData.role === 'compliance-officer';

  // Handle scroll detection for glassy effect
  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.scrollY;
      setIsScrolled(scrollTop > 10); // Start glassy effect after 10px scroll
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('client_id');
    localStorage.removeItem('client_name');
    localStorage.removeItem('client_email');
    localStorage.removeItem('user');
    localStorage.removeItem('client_id_list');
    localStorage.removeItem('selected_client_id');
    window.location.href = '/';
  };

  // Handle client selection for compliance officers
  const handleClientSelection = (clientId) => {
    localStorage.setItem('selected_client_id', clientId);
    clearRiskAssessmentClientIdCache(); // Clear cache when client changes
    setShowClientDropdown(false);
    // Optionally refresh the current page to use the new client_id
    window.location.reload();
  };

  // Get current selected client or default
  const getCurrentClientId = () => {
    if (isComplianceOfficer) {
      return localStorage.getItem('selected_client_id') || Object.values(clientIdList)[0] || '';
    }
    return userData.client_id || '';
  };

  // Handle role selection with mode-based routing
  const handleRoleSelection = (role) => {
    if (modalMode === 'login') {
      // Login mode - go to login pages
      if (role === 'admin') {
        navigate('/login');
      } else if (role === 'compliance_officer') {
        navigate('/role-login');
      }
    } else {
      // Signup mode (default) - go to signup pages
      if (role === 'admin') {
        navigate('/signup');
      } else if (role === 'compliance_officer') {
        navigate('/role-signup');
      }
    }
  };

  return (
    <header className={`main-header ${isScrolled ? 'scrolled' : ''}`}>
      <div className="header-left-section">
        <div className="mobile-nav">
          <HorizontalMenu showAuthButtons={true} />
        </div>
        <div className="header-logo-section">
          <img src="/aip_logo.jpg" alt="AIInsight Logo" className="header-logo" />
          <div className="header-brand">
            <span className="header-brand-name">AIPlaneTech</span>
            <span className="header-brand-separator">|</span>
            <span className="product-name">AI-Insight-Pro</span>
          </div>
        </div>
      </div>
      <div className="desktop-nav">
        <HorizontalMenu showAuthButtons={false} />
      </div>
      <div className="header-right-section">
        {/* <ThemeToggle /> */}
        <div className="desktop-auth">
          {currentUserName || userData.username ? (
            <div className="auth-buttons-container">
              {/* Client Dropdown for Compliance Officers */}
              {isComplianceOfficer && Object.keys(clientIdList).length > 0 && (
                <div className="client-dropdown" style={{ position: 'relative', marginRight: '1rem' }}>
                  <button
                    onClick={() => setShowClientDropdown(!showClientDropdown)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      padding: '0.5rem 1rem',
                      border: '1px solid var(--border)',
                      borderRadius: '0.375rem',
                      background: 'var(--background)',
                      color: 'var(--foreground)',
                      cursor: 'pointer',
                      fontSize: '0.875rem',
                      gap: '0.5rem'
                    }}
                  >
                    <span>
                      {Object.keys(clientIdList).find(username =>
                        clientIdList[username] === getCurrentClientId()
                      ) || 'Select Client'}
                    </span>
                    <ChevronDown size={16} />
                  </button>

                  {showClientDropdown && (
                    <div style={{
                      position: 'absolute',
                      top: '100%',
                      left: 0,
                      right: 0,
                      background: 'var(--background)',
                      border: '1px solid var(--border)',
                      borderRadius: '0.375rem',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                      zIndex: 10000,
                      marginTop: '0.25rem'
                    }}>
                      {Object.entries(clientIdList).map(([username, clientId]) => (
                        <button
                          key={clientId}
                          onClick={() => handleClientSelection(clientId)}
                          style={{
                            display: 'block',
                            width: '100%',
                            padding: '0.5rem 1rem',
                            border: 'none',
                            background: getCurrentClientId() === clientId ? 'var(--accent)' : 'transparent',
                            color: getCurrentClientId() === clientId ? 'var(--accent-foreground)' : 'var(--foreground)',
                            textAlign: 'left',
                            cursor: 'pointer',
                            fontSize: '0.875rem'
                          }}
                          onMouseEnter={(e) => {
                            if (getCurrentClientId() !== clientId) {
                              e.target.style.background = 'var(--muted)';
                            }
                          }}
                          onMouseLeave={(e) => {
                            if (getCurrentClientId() !== clientId) {
                              e.target.style.background = 'transparent';
                            }
                          }}
                        >
                          {username}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <Link to="/profile" className="header-profile-link" title={currentUserName || userData.username}>
                <UserCircle size={20} style={{ marginRight: '0.5rem' }} />
                <span>{currentUserName || userData.username}</span>
              </Link>
              <button onClick={handleLogout} className="logout-btn" title="Logout">
                <LogOut size={18} style={{ marginRight: '0.4rem' }} />
                <span>Logout</span>
              </button>
            </div>
          ) : (
            <div className="auth-buttons-container">
              <button onClick={() => {
                setModalMode('login');
                setShowRoleSelection(true);
              }} className="header-login-btn" style={{
                marginRight: '0.5rem',
                padding: '0.5rem 1rem',
                border: '1px solid var(--border)',
                borderRadius: '0.375rem',
                background: 'transparent',
                color: 'var(--foreground)',
                fontSize: '0.875rem',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}>
                Log In
              </button>
              <button onClick={() => {
                setModalMode('signup');
                setShowRoleSelection(true);
              }} className="header-signup-btn">
                Sign Up
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Role Selection Modal */}
      <RoleSelectionModal
        isOpen={showRoleSelection}
        onClose={() => setShowRoleSelection(false)}
        onRoleSelect={handleRoleSelection}
        title="Choose Your Role"
        subtitle={modalMode === 'login'
          ? 'Select the type of account you want to log in to'
          : 'Select the type of account you want to create'
        }
      />
    </header>
  );
};

export default Header;