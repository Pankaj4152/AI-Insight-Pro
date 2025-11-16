import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { UserCheck, Building, X } from 'lucide-react';

const RoleSelectionModal = ({ 
  isOpen, 
  onClose, 
  onRoleSelect,
  title = "Choose Your Role",
  subtitle = "Select your role to get started with the appropriate access level"
}) => {
  const navigate = useNavigate();

  // Prevent body scroll when modal is open and ensure proper centering
  useEffect(() => {
    if (isOpen) {
      // Prevent body scroll
      document.body.style.overflow = 'hidden';
      document.body.style.paddingRight = '0px'; // Prevent layout shift
      
      // Add keyboard support
      const handleKeyDown = (event) => {
        if (event.key === 'Escape') {
          onClose();
        }
      };
      
      document.addEventListener('keydown', handleKeyDown);
      
      // Ensure modal appears in viewport center
      const modalContainer = document.querySelector('[data-modal="role-selection"]');
      if (modalContainer) {
        modalContainer.focus();
      }
      
      return () => {
        // Restore body scroll
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
        document.removeEventListener('keydown', handleKeyDown);
      };
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleRoleSelection = (role) => {
    onClose();
    
    if (onRoleSelect) {
      onRoleSelect(role);
    } else {
      // Default navigation behavior
      if (role === 'admin') {
        navigate('/signup');
      } else if (role === 'compliance_officer') {
        navigate('/role-signup');
      }
    }
  };

  return (
    <div 
      data-modal="role-selection"
      tabIndex={-1}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 9999,
        animation: 'fadeIn 0.3s ease-out',
        margin: 0,
        padding: '1rem',
        boxSizing: 'border-box',
        outline: 'none'
      }}
      onClick={(e) => {
        // Close modal when clicking backdrop
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div style={{
        backgroundColor: 'white',
        borderRadius: '1rem',
        padding: '2rem',
        maxWidth: '500px',
        width: '100%',
        maxHeight: '90vh',
        overflowY: 'auto',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        position: 'relative',
        transform: 'scale(1)',
        animation: 'slideIn 0.3s ease-out',
        margin: 'auto'
      }}>
        {/* Close Button */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '1rem',
            right: '1rem',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: '#6B7280',
            padding: '0.5rem',
            borderRadius: '0.5rem',
            transition: 'all 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.target.style.backgroundColor = 'rgba(107, 114, 128, 0.1)';
          }}
          onMouseLeave={(e) => {
            e.target.style.backgroundColor = 'transparent';
          }}
        >
          <X size={24} />
        </button>

        <h2 style={{
          fontSize: '1.5rem',
          fontWeight: '600',
          color: 'hsl(215 25% 15%)',
          marginBottom: '1rem',
          textAlign: 'center'
        }}>
          {title}
        </h2>

        <p style={{
          color: 'hsl(215 16% 47%)',
          textAlign: 'center',
          marginBottom: '2rem'
        }}>
          {subtitle}
        </p>

        <div style={{
          display: 'flex',
          gap: '1rem',
          flexDirection: 'column'
        }}>
          {/* Admin Button */}
          <button
            onClick={() => handleRoleSelection('admin')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '1rem',
              padding: '1.5rem',
              border: '2px solid #000',
              borderRadius: '0.75rem',
              backgroundColor: 'white',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              width: '100%',
              color: 'black'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#19BCB3';
              e.currentTarget.style.color = 'white';
              e.currentTarget.style.borderColor = '#19BCB3';
              e.currentTarget.style.transform = 'translateY(-2px)';
              const icon = e.currentTarget.querySelector('svg');
              const title = e.currentTarget.querySelector('h3');
              const desc = e.currentTarget.querySelector('p');
              if (icon) icon.style.color = 'white';
              if (title) title.style.color = 'white';
              if (desc) desc.style.color = 'white';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'white';
              e.currentTarget.style.color = 'black';
              e.currentTarget.style.borderColor = '#000';
              e.currentTarget.style.transform = 'translateY(0)';
              const icon = e.currentTarget.querySelector('svg');
              const title = e.currentTarget.querySelector('h3');
              const desc = e.currentTarget.querySelector('p');
              if (icon) icon.style.color = 'black';
              if (title) title.style.color = 'black';
              if (desc) desc.style.color = 'hsl(215 16% 47%)';
            }}
          >
            <UserCheck size={32} style={{ color: 'inherit' }} />
            <div style={{ textAlign: 'left' }}>
              <h3 style={{
                margin: 0,
                fontSize: '1.2rem',
                fontWeight: '600',
                color: 'inherit'
              }}>
                Admin
              </h3>
              <p style={{
                margin: 0,
                fontSize: '0.9rem',
                color: 'hsl(215 16% 47%)',
                transition: 'color 0.3s ease'
              }}>
                Full system access and management capabilities
              </p>
            </div>
          </button>

          {/* Compliance Officer Button */}
          <button
            onClick={() => handleRoleSelection('compliance_officer')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '1rem',
              padding: '1.5rem',
              border: '2px solid #000',
              borderRadius: '0.75rem',
              backgroundColor: 'white',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              width: '100%',
              color: 'black'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#19BCB3';
              e.currentTarget.style.color = 'white';
              e.currentTarget.style.borderColor = '#19BCB3';
              e.currentTarget.style.transform = 'translateY(-2px)';
              const icon = e.currentTarget.querySelector('svg');
              const title = e.currentTarget.querySelector('h3');
              const desc = e.currentTarget.querySelector('p');
              if (icon) icon.style.color = 'white';
              if (title) title.style.color = 'white';
              if (desc) desc.style.color = 'white';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'white';
              e.currentTarget.style.color = 'black';
              e.currentTarget.style.borderColor = '#000';
              e.currentTarget.style.transform = 'translateY(0)';
              const icon = e.currentTarget.querySelector('svg');
              const title = e.currentTarget.querySelector('h3');
              const desc = e.currentTarget.querySelector('p');
              if (icon) icon.style.color = 'black';
              if (title) title.style.color = 'black';
              if (desc) desc.style.color = 'hsl(215 16% 47%)';
            }}
          >
            <Building size={32} style={{ color: 'inherit' }} />
            <div style={{ textAlign: 'left' }}>
              <h3 style={{
                margin: 0,
                fontSize: '1.2rem',
                fontWeight: '600',
                color: 'inherit'
              }}>
                Compliance Officer
              </h3>
              <p style={{
                margin: 0,
                fontSize: '0.9rem',
                color: 'hsl(215 16% 47%)',
                transition: 'color 0.3s ease'
              }}>
                Monitor and manage compliance across multiple clients
                <span style={{
                  display: 'block',
                  color: 'inherit',
                  fontSize: '0.8rem',
                  marginTop: '0.5rem'
                }}>
                  Please ensure the company has at least one active admin account before proceeding
                </span>
              </p>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};

export default RoleSelectionModal;
