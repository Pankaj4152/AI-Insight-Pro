import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../Css/Signup.css';
import { API_LOGIN_URL } from '../apiConfig';

// Add responsive styles for LoginPage
const loginResponsiveStyles = `
  @media (max-width: 768px) {
    .login-form-mobile {
      padding: 1.5rem !important;
      max-width: 90vw !important;
    }
  }
  
  @media (max-width: 480px) {
    .login-form-mobile {
      padding: 1rem !important;
      border-radius: 0.5rem !important;
    }
  }
`;

// Inject styles
if (typeof document !== 'undefined') {
  const styleElement = document.createElement('style');
  styleElement.textContent = loginResponsiveStyles;
  if (!document.head.querySelector('[data-login-responsive]')) {
    styleElement.setAttribute('data-login-responsive', 'true');
    document.head.appendChild(styleElement);
  }
}

function LoginPage({ setUser }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [validationError, setValidationError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const validateEmail = (email) => {
    return /^[^\s@]+@[^"\s]+\.[^\s@]+$/.test(email);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setValidationError('');
    if (!validateEmail(email)) {
      setValidationError('Please enter a valid email address.');
      return;
    }
    if (!password) {
      setValidationError('Password cannot be empty.');
      return;
    }
    setLoading(true);
    try {
      const response = await fetch(`${API_LOGIN_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(),
          password: password
        })
      });
      const data = await response.json();
      console.log('Login API response:', data); 
      if (!response.ok) {
        setValidationError(data.detail || 'Login failed.');
      } else {
 
        // --- THIS IS THE FIX ---
        // Save all necessary items to localStorage after a successful login
        localStorage.setItem('client_id', data.client_id); // <-- THE MISSING LINE
        localStorage.setItem('client_name', data.username);
        localStorage.setItem('client_email', data.email);
        
        // Also store the complete user object with client_id
        const userObject = {
          name: data.username,
          email: data.email,
          client_id: data.client_id
        };
        localStorage.setItem('user', JSON.stringify(userObject));
        
        // Update the app's user state
        setUser(userObject);
        
        // Navigate to the dashboard
        navigate('/connect');
      }
    } catch (error) {
      setValidationError('Error connecting to server.');
    }
    setLoading(false);
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--background)',
      color: 'var(--foreground)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 'clamp(1rem, 4vw, 2rem)',
      fontFamily: 'var(--font-family)'
    }}>
      <div className="login-form-mobile" style={{
        background: 'var(--card)',
        borderRadius: '1rem',
        padding: 'clamp(2rem, 5vw, 3rem)',
        width: '100%',
        maxWidth: '420px',
        boxShadow: 'var(--shadow-lg)',
        border: '1px solid var(--border)'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{
            color: 'var(--primary)',
            fontSize: 'clamp(1.5rem, 4vw, 2rem)',
            fontWeight: '700',
            marginBottom: '0.5rem'
          }}>
            Welcome Back
          </h1>
          <p style={{
            color: 'var(--muted-foreground)',
            fontSize: 'clamp(0.9rem, 2.5vw, 1rem)'
          }}>
            Enter your credentials to access your account
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div>
            <label htmlFor="email" style={{
              display: 'block',
              marginBottom: '0.5rem',
              fontWeight: '500',
              color: 'var(--foreground)'
            }}>
              Email Address
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="Enter your email"
              style={{
                width: '100%',
                padding: '0.75rem 1rem',
                border: '1px solid var(--border)',
                borderRadius: '0.5rem',
                fontSize: '1rem',
                outline: 'none',
                transition: 'border-color 0.2s ease',
                boxSizing: 'border-box',
                background: 'var(--background)',
                color: 'var(--foreground)'
              }}
              onFocus={(e) => e.target.style.borderColor = 'var(--primary)'}
              onBlur={(e) => e.target.style.borderColor = 'var(--border)'}
            />
          </div>

          <div>
            <label htmlFor="password" style={{
              display: 'block',
              marginBottom: '0.5rem',
              fontWeight: '500',
              color: 'var(--foreground)'
            }}>
              Password
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Enter your password"
              style={{
                width: '100%',
                padding: '0.75rem 1rem',
                border: '1px solid var(--border)',
                borderRadius: '0.5rem',
                fontSize: '1rem',
                outline: 'none',
                transition: 'border-color 0.2s ease',
                boxSizing: 'border-box',
                background: 'var(--background)',
                color: 'var(--foreground)'
              }}
              onFocus={(e) => e.target.style.borderColor = 'var(--primary)'}
              onBlur={(e) => e.target.style.borderColor = 'var(--border)'}
            />
          </div>

          {validationError && (
            <div style={{
              padding: '0.75rem',
              backgroundColor: 'var(--destructive)',
              borderRadius: '0.5rem',
              border: '1px solid var(--destructive)',
              color: 'var(--destructive-foreground)',
              fontSize: '0.9rem'
            }}>
              {validationError}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '0.875rem',
              backgroundColor: loading ? 'var(--muted)' : 'var(--primary)',
              color: 'var(--primary-foreground)',
              border: 'none',
              borderRadius: '0.5rem',
              fontSize: '1rem',
              fontWeight: '600',
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s ease',
              opacity: loading ? 0.7 : 1
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                e.target.style.backgroundColor = 'var(--primary-hover)';
                e.target.style.transform = 'translateY(-1px)';
              }
            }}
            onMouseLeave={(e) => {
              if (!loading) {
                e.target.style.backgroundColor = 'var(--primary)';
                e.target.style.transform = 'translateY(0)';
              }
            }}
          >
            {loading ? 'Signing In...' : 'Sign In'}
          </button>
        </form>

        <div style={{
          textAlign: 'center',
          marginTop: '2rem',
          color: 'var(--muted-foreground)'
        }}>
          Don't have an account?{' '}
          <button
            onClick={() => navigate('/signup')}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--primary)',
              cursor: 'pointer',
              fontWeight: '600',
              textDecoration: 'underline'
            }}
            onMouseEnter={(e) => e.target.style.color = 'var(--primary-hover)'}
            onMouseLeave={(e) => e.target.style.color = 'var(--primary)'}
          >
            Sign up here
          </button>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;