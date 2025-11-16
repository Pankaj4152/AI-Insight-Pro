import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, MapPin, Home, Contact, User, Shield, FileText, Cookie, HelpCircle } from 'lucide-react';
import RoleSelectionModal from './RoleSelectionModal';
import '../Css/App.css';

const Footer = () => {
  const navigate = useNavigate();
  const [showRoleSelection, setShowRoleSelection] = useState(false);
  const [pendingRoute, setPendingRoute] = useState('');

  // Check if user is logged in
  const isLoggedIn = localStorage.getItem('client_email') || localStorage.getItem('client_name');

  const handleEmailClick = () => {
    window.location.href = 'mailto:aiplantech@aipglobal.in';
  };

  const handleServiceClick = (route, e) => {
    e.preventDefault();
    
    if (isLoggedIn) {
      // User is logged in, navigate directly
      navigate(route);
    } else {
      // User is not logged in, show role selection modal for login
      setPendingRoute(route);
      setShowRoleSelection(true);
    }
  };

  const handleRoleSelection = (role) => {
    // After role selection for login, navigate to login pages
    if (role === 'admin') {
      navigate('/login', { state: { redirectTo: pendingRoute } });
    } else if (role === 'compliance_officer') {
      navigate('/role-login', { state: { redirectTo: pendingRoute } });
    }
    setPendingRoute('');
  };

  return (
    <footer className="main-footer">
      <div className="footer-content">
        {/* Company Info Section */}
        <div className="footer-section">
          <div className="footer-brand">
            <img src="/aip_logo.jpg" alt="AIPlaneTech Logo" className="footer-logo" />
            <div className="footer-brand-text">
              <h3>AIPlaneTech | AI-Insight-Pro</h3>
              <p className="footer-tagline">
                Pioneering AI-Powered Data Protection and Risk Assessment Solutions
              </p>
            </div>
          </div>
          
          <div className="footer-contact">
            <div className="contact-item" onClick={handleEmailClick}>
              <Mail className="contact-icon" />
              <span>aiplantech@aipglobal.in</span>
            </div>
            <div className="contact-item">
              <MapPin className="contact-icon" />
              <span>Jodhpur, Rajasthan, India</span>
            </div>
          </div>
        </div>

        {/* Quick Links Section */}
        <div className="footer-section">
          <h4>Quick Links</h4>
          <ul className="footer-links">
            <li><Link to="/">Home</Link></li>
            <li><Link to="/about">About</Link></li>
            <li><Link to="/contact">Contact</Link></li>
            <li><Link to="/how-to-use">How to Use</Link></li>
          </ul>
        </div>

        {/* Legal Section */}
        <div className="footer-section">
          <h4>Legal</h4>
          <ul className="footer-links">
            <li><Link to="/">Privacy Policy</Link></li>
            <li><Link to="/">Terms of Service</Link></li>
            <li><Link to="/">Cookie Policy</Link></li>
            <li><Link to="/">Support</Link></li>
          </ul>
        </div>

        {/* Services Section */}
        <div className="footer-section">
          <h4>Services</h4>
          <ul className="footer-links">
            <li>
              <a 
                href="/risk-assessment" 
                onClick={(e) => handleServiceClick('/risk-assessment', e)}
                style={{ cursor: 'pointer' }}
              >
                Risk Assessment
              </a>
            </li>
            <li>
              <a 
                href="/sde-catalogue" 
                onClick={(e) => handleServiceClick('/sde-catalogue', e)}
                style={{ cursor: 'pointer' }}
              >
                SDE Catalogue
              </a>
            </li>
            <li>
              <a 
                href="/dashboard" 
                onClick={(e) => handleServiceClick('/dashboard', e)}
                style={{ cursor: 'pointer' }}
              >
                Dashboard
              </a>
            </li>
            <li>
              <a 
                href="/report" 
                onClick={(e) => handleServiceClick('/report', e)}
                style={{ cursor: 'pointer' }}
              >
                Reports
              </a>
            </li>
          </ul>
          <p className="services-note">
            * Services require sign-in
          </p>
        </div>
      </div>

      {/* Copyright Section */}
      <div className="footer-bottom">
        <div className="copyright">
          © 2025 AIPlaneTech - AI-Insight-Pro. All rights reserved.
        </div>
      </div>

      {/* Role Selection Modal for Service Access */}
      <RoleSelectionModal
        isOpen={showRoleSelection}
        onClose={() => {
          setShowRoleSelection(false);
          setPendingRoute('');
        }}
        onRoleSelect={handleRoleSelection}
        title="Sign In to Access Service"
        subtitle="Please select your account type to sign in and access this service"
      />
    </footer>
  );
};

export default Footer; 