import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, EyeOff, CheckCircle, X } from 'lucide-react';
import { API_LOGIN_URL } from '../apiConfig';

function RoleSignupPage() {
  const navigate = useNavigate();
  
  // Form states
  const [step, setStep] = useState(1); // 1: Basic Info, 2: Company & Admin Verification
  const [formData, setFormData] = useState({
    fullName: '',
    username: '',
    email: '',
    password: '',
    companyName: ''
  });
  
  // UI states
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [companyVerified, setCompanyVerified] = useState(false);
  const [verifiedAdmins, setVerifiedAdmins] = useState([]);
  const [currentAdmin, setCurrentAdmin] = useState({ username: '', email: '' });
  const [adminVerifying, setAdminVerifying] = useState(false);

  // Handle input changes
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  // Validate basic info
  const validateBasicInfo = () => {
    const newErrors = {};
    
    if (!formData.fullName.trim()) newErrors.fullName = 'Full name is required';
    if (!formData.username.trim()) newErrors.username = 'Username is required';
    if (!formData.email.trim()) newErrors.email = 'Email is required';
    if (!formData.password) newErrors.password = 'Password is required';
    if (formData.password.length < 6) newErrors.password = 'Password must be at least 6 characters';
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (formData.email && !emailRegex.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle continue to step 2
  const handleContinue = () => {
    if (validateBasicInfo()) {
      setStep(2);
    }
  };

  // Check company exists
  const checkCompany = async () => {
    if (!formData.companyName.trim()) {
      setErrors(prev => ({ ...prev, companyName: 'Company name is required' }));
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_LOGIN_URL}/compliance-officer/check-company`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company_name: formData.companyName })
      });

      if (response.ok) {
        setCompanyVerified(true);
        setErrors(prev => ({ ...prev, companyName: '' }));
      } else {
        const errorData = await response.json();
        setErrors(prev => ({ ...prev, companyName: errorData.detail || 'Company not found' }));
        setCompanyVerified(false);
      }
    } catch (error) {
      setErrors(prev => ({ ...prev, companyName: 'Error verifying company' }));
      setCompanyVerified(false);
    } finally {
      setLoading(false);
    }
  };

  // Remove verified admin
  const removeAdmin = (indexToRemove) => {
    setVerifiedAdmins(prev => prev.filter((_, index) => index !== indexToRemove));
  };

  // Verify admin
  const verifyAdmin = async () => {
    if (!currentAdmin.username.trim() || !currentAdmin.email.trim()) {
      setErrors(prev => ({ ...prev, admin: 'Both admin username and email are required' }));
      return;
    }

    setAdminVerifying(true);
    try {
      const response = await fetch(`${API_LOGIN_URL}/compliance-officer/verify-admin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          admin_username: currentAdmin.username,
          admin_email: currentAdmin.email,
          company_name: formData.companyName
        })
      });

      if (response.ok) {
        const data = await response.json();
        setVerifiedAdmins(prev => [...prev, {
          admin_username: currentAdmin.username,
          admin_email: currentAdmin.email,
          admin_client_id: data.admin_client_id
        }]);
        setCurrentAdmin({ username: '', email: '' });
        setErrors(prev => ({ ...prev, admin: '' }));
      } else {
        const errorData = await response.json();
        setErrors(prev => ({ ...prev, admin: errorData.detail || 'Admin verification failed' }));
      }
    } catch (error) {
      setErrors(prev => ({ ...prev, admin: 'Error verifying admin' }));
    } finally {
      setAdminVerifying(false);
    }
  };

  // Handle final signup
  const handleSignup = async () => {
    if (verifiedAdmins.length === 0) {
      setErrors(prev => ({ ...prev, admin: 'At least one admin must be verified' }));
      return;
    }

    setLoading(true);
    try {
      // Convert verified admins to the expected format
      const adminCredentials = verifiedAdmins.map(admin => ({
        admin_username: admin.admin_username,
        admin_email: admin.admin_email
      }));

      const response = await fetch(`${API_LOGIN_URL}/compliance-officer/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: formData.fullName,
          username: formData.username,
          email: formData.email,
          password: formData.password,
          company_name: formData.companyName,
          admin_credentials: adminCredentials
        })
      });

      if (response.ok) {
        const data = await response.json();
        // Redirect to compliance login
        navigate('/role-login', {
          state: {
            message: data.message || 'Account created successfully! Please log in.',
            email: formData.email
          }
        });
      } else {
        const errorData = await response.json();
        setErrors(prev => ({ ...prev, signup: errorData.detail || 'Signup failed' }));
      }
    } catch (error) {
      setErrors(prev => ({ ...prev, signup: 'Error creating account' }));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>Compliance Officer Signup</h1>
          <p>Create your compliance officer account</p>
        </div>

        {step === 1 ? (
          // Step 1: Basic Information
          <div className="auth-form">
            <div className="form-group">
              <label htmlFor="fullName">Full Name</label>
              <input
                type="text"
                id="fullName"
                name="fullName"
                value={formData.fullName}
                onChange={handleInputChange}
                placeholder="Enter your full name"
                className={errors.fullName ? 'error' : ''}
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
              {errors.fullName && <span className="error-message">{errors.fullName}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="username">Username</label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleInputChange}
                placeholder="Choose a username"
                className={errors.username ? 'error' : ''}
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
              {errors.username && <span className="error-message">{errors.username}</span>}
            </div>

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
                  placeholder="Create a password"
                  className={errors.password ? 'error' : ''}
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

            <button
              type="button"
              className="auth-button"
              onClick={handleContinue}
              disabled={loading}
            >
              Continue
            </button>

            <div className="auth-footer">
              <p>
                Already have an account?{' '}
                <button
                  type="button"
                  className="link-button"
                  onClick={() => navigate('/role-login')}
                >
                  Log in
                </button>
              </p>
            </div>
          </div>
        ) : (
          // Step 2: Company & Admin Verification
          <div className="auth-form">
            <div className="form-group">
              <label htmlFor="companyName">Company Name</label>
              <div style={{ position: 'relative' }}>
                <input
                  type="text"
                  id="companyName"
                  name="companyName"
                  value={formData.companyName}
                  onChange={handleInputChange}
                  placeholder="Enter company name"
                  className={errors.companyName ? 'error' : companyVerified ? 'success' : ''}
                  style={{
                    width: 'calc(100% - 6rem)',
                    padding: '0.75rem 6rem 0.75rem 0.75rem',
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
                  onClick={checkCompany}
                  disabled={loading || !formData.companyName.trim()}
                  style={{
                    position: 'absolute',
                    right: '0.5rem',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'var(--primary)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '0.375rem',
                    padding: '0.5rem 0.75rem',
                    fontSize: '0.75rem',
                    cursor: 'pointer'
                  }}
                >
                  {loading ? 'Verifying...' : companyVerified ? 'Verified' : 'Verify'}
                </button>
              </div>
              {errors.companyName && <span className="error-message">{errors.companyName}</span>}
              {companyVerified && <span className="success-message">Company verified successfully!</span>}
            </div>

            {companyVerified && (
              <>
                <div className="admin-section">
                  <h3>Add Admin for Verification</h3>
                  <p>Add at least one admin to verify your access to this company.</p>

                  <div className="form-group">
                    <label>Admin Username</label>
                    <input
                      type="text"
                      value={currentAdmin.username}
                      onChange={(e) => setCurrentAdmin(prev => ({ ...prev, username: e.target.value }))}
                      placeholder="Admin username"
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
                  </div>

                  <div className="form-group">
                    <label>Admin Email</label>
                    <input
                      type="email"
                      value={currentAdmin.email}
                      onChange={(e) => setCurrentAdmin(prev => ({ ...prev, email: e.target.value }))}
                      placeholder="Admin email"
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
                  </div>

                  <div className="form-actions">
                    <button
                      type="button"
                      className="auth-button secondary"
                      onClick={verifyAdmin}
                      disabled={adminVerifying || !currentAdmin.username.trim() || !currentAdmin.email.trim()}
                    >
                      {adminVerifying ? 'Verifying...' : 'Verify & Add Admin'}
                    </button>
                  </div>

                  {errors.admin && <span className="error-message">{errors.admin}</span>}
                </div>

                {verifiedAdmins.length > 0 && (
                  <div className="verified-admins">
                    <h4>Verified Admins ({verifiedAdmins.length})</h4>
                    {verifiedAdmins.map((admin, index) => (
                      <div key={index} className="verified-admin-item">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1 }}>
                          <CheckCircle size={16} color="#10B981" />
                          <span>{admin.admin_username} ({admin.admin_email})</span>
                        </div>
                        <button
                          type="button"
                          onClick={() => removeAdmin(index)}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: '#EF4444',
                            cursor: 'pointer',
                            padding: '0.25rem',
                            borderRadius: '0.25rem',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                          }}
                          title="Remove admin"
                        >
                          <X size={16} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                <div className="form-actions">
                  <button
                    type="button"
                    className="auth-button secondary"
                    onClick={() => setStep(1)}
                  >
                    Back
                  </button>
                  <button
                    type="button"
                    className="auth-button"
                    onClick={handleSignup}
                    disabled={loading || verifiedAdmins.length === 0}
                  >
                    {loading ? 'Creating Account...' : 'Create Account'}
                  </button>
                </div>

                {errors.signup && <span className="error-message">{errors.signup}</span>}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default RoleSignupPage;
