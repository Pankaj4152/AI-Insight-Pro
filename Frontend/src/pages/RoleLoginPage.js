import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Eye, EyeOff, AlertCircle, CheckCircle } from 'lucide-react';
import { API_LOGIN_URL } from '../apiConfig';

function RoleLoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Form states
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  
  // UI states
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState('');

  // Check for success message from signup
  useEffect(() => {
    if (location.state?.message) {
      setMessage(location.state.message);
      if (location.state?.email) {
        setFormData(prev => ({ ...prev, email: location.state.email }));
      }
    }
  }, [location.state]);

  // Handle input changes
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  // Validate form
  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.email.trim()) newErrors.email = 'Email is required';
    if (!formData.password) newErrors.password = 'Password is required';
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (formData.email && !emailRegex.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle login
  const handleLogin = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setLoading(true);
    setErrors({});

    try {
      const response = await fetch(`${API_LOGIN_URL}/compliance-officer/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password
        })
      });

      if (response.ok) {
        const data = await response.json();

        // Store user data in localStorage
        const userData = {
          idToken: data.idToken,
          email: data.email,
          username: data.username,
          client_id: data.client_id,
          role: data.role,
          client_id_list: data.client_id_list || {}
        };

        localStorage.setItem('user', JSON.stringify(userData));

        // Store client_id separately for compatibility with existing code
        localStorage.setItem('client_id', data.client_id);

        // Store the client_id_list separately for easy access
        if (data.client_id_list) {
          localStorage.setItem('client_id_list', JSON.stringify(data.client_id_list));
        }

        // Store client_name for compatibility with existing code
        localStorage.setItem('client_name', data.username);

        // Redirect to dashboard
        navigate('/dashboard');
      } else {
        const errorData = await response.json();
        setErrors({ login: errorData.detail || 'Login failed' });
      }
    } catch (error) {
      setErrors({ login: 'Network error. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>Compliance Officer Login</h1>
          <p>Sign in to your compliance officer account</p>
        </div>

        {message && (
          <div className="message success">
            <CheckCircle size={20} />
            <span>{message}</span>
          </div>
        )}

        <form className="auth-form" onSubmit={handleLogin}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              placeholder="Enter your email"
              className={errors.email ? 'error' : ''}
              autoComplete="email"
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid var(--border)',
                borderRadius: '0.5rem',
                background: 'var(--background)',
                color: 'var(--foreground)',
                fontSize: '0.875rem'
              }}
            />
            {errors.email && <span className="error-message">{errors.email}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="Enter your password"
                className={errors.password ? 'error' : ''}
                autoComplete="current-password"
                style={{
                  width: 'calc(100% - 3rem)',
                  padding: '0.75rem 3rem 0.75rem 0.75rem',
                  border: '1px solid var(--border)',
                  borderRadius: '0.5rem',
                  background: 'var(--background)',
                  color: 'var(--foreground)',
                  fontSize: '0.875rem',
                  boxSizing: 'border-box'
                }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '0.75rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  color: 'var(--muted-foreground)',
                  cursor: 'pointer',
                  padding: '0.25rem'
                }}
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
            {errors.password && <span className="error-message">{errors.password}</span>}
          </div>

          {errors.login && (
            <div className="message error">
              <AlertCircle size={20} />
              <span>{errors.login}</span>
            </div>
          )}

          <button
            type="submit"
            className="auth-button"
            disabled={loading}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>

          <div className="auth-footer">
            <p>
              Don't have an account?{' '}
              <button
                type="button"
                className="link-button"
                onClick={() => navigate('/role-signup')}
              >
                Sign up
              </button>
            </p>
            <p>
              Are you an admin?{' '}
              <button
                type="button"
                className="link-button"
                onClick={() => navigate('/login')}
              >
                Admin Login
              </button>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}

export default RoleLoginPage;
