import React, { useState, useEffect } from 'react';
import '../Css/Signup.css';
import { useNavigate } from 'react-router-dom';
import { API_LOGIN_URL } from '../apiConfig';

function SignupPage({ setUser }) {
  const [step, setStep] = useState(1);
  const [fullName, setFullName] = useState('');
  const [clientName, setClientName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [industry, setIndustry] = useState('');
  const [customIndustry, setCustomIndustry] = useState('');
  const [country, setCountry] = useState('');
  const [validationError, setValidationError] = useState('');
  const [submissionMessage, setSubmissionMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const signupContainer = document.getElementById('signup-container');
    if (signupContainer) signupContainer.classList.add('fade-in');
  }, []);

  useEffect(() => {
    if (submissionMessage.toLowerCase().includes('successful')) {
      setShowToast(true);
      const timer = setTimeout(() => {
        setShowToast(false);
        // Set signup flow state and redirect to SDE Catalogue
        localStorage.setItem('signup_flow', 'in_progress');
        localStorage.setItem('signup_step', 'sde_catalogue');
        navigate('/sde-catalogue');
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [submissionMessage, navigate]);

  useEffect(() => {
    const fetchCountry = async () => {
      try {
        const res = await fetch('https://ipapi.co/json/');
        const data = await res.json();
        setCountry(data.country_name || '');
      } catch {
        setCountry('');
      }
    };
    fetchCountry();
  }, []);

  const validateStep1 = () => {
    if (!fullName.trim()) return 'Full name is required.';
    if (!clientName.trim()) return 'Username is required.';
    if (!email.trim()) return 'Email is required.';
    if (!password || password.length < 6) return 'Password must be at least 6 characters.';
    return '';
  };

  const validateStep2 = () => {
    if (!companyName.trim()) return 'Company name is required.';
    if (!industry || (industry === 'Other' && !customIndustry.trim())) return 'Please select or enter an industry.';
    if (!country.trim()) return 'Country is required.';
    return '';
  };

  const handleNext = (e) => {
    e.preventDefault();
    const error = validateStep1();
    if (error) {
      setValidationError(error);
    } else {
      setValidationError('');
      setStep(2);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const error = validateStep2();
    if (error) {
      setValidationError(error);
      return;
    }

    setLoading(true);
    setValidationError('');
    setSubmissionMessage('');

    try {
      console.log('Sending signup request to:', `${API_LOGIN_URL}/signup`);
      console.log('Request payload:', {
        full_name: fullName.trim(),
        username: clientName.trim(),
        email: email.trim(),
        company_name: companyName.trim(),
        password: '***hidden***', // Don't log actual password
        industry: industry === 'Other' ? customIndustry.trim() : industry,
        country: country.trim(),
      });
      
      const response = await fetch(`${API_LOGIN_URL}/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: fullName.trim(),
          username: clientName.trim(),
          email: email.trim(),
          company_name: companyName.trim(),
          password: password,
          industry: industry === 'Other' ? customIndustry.trim() : industry,
          country: country.trim()
        })
      });

      const data = await response.json();
      if (!response.ok) {
        if (Array.isArray(data.detail)) {
          setValidationError(data.detail.map(e => e.msg).join(' '));
        } else if (typeof data.detail === 'string') {
          setValidationError(data.detail);
        } else {
          setValidationError(JSON.stringify(data));
        }
      } else {
        // Store all signup data after successful registration
        console.log('Signup successful, response data:', data); // Debug log
        
        // Check email sending status
        if (data.email_sent === false) {
          console.warn('Email was not sent during signup');
          // You could optionally show a non-blocking warning to the user
        } else {
          console.log('Welcome email should have been sent');
        }
        
        // First check if we got client_id from the response
        if (data.client_id) {
          localStorage.setItem('client_id', data.client_id);
          console.log('Stored client_id:', data.client_id); // Debug log
        } else {
          console.warn('No client_id in signup response'); // Debug log
        }
        
        localStorage.setItem('client_name', clientName.trim());
        localStorage.setItem('client_email', email.trim());
        localStorage.setItem('signup_full_name', fullName.trim());
        localStorage.setItem('signup_company', companyName.trim());
        localStorage.setItem('signup_industry', industry === 'Other' ? customIndustry.trim() : industry);
        localStorage.setItem('signup_country', country.trim());
        // Store profile_industry for SDE catalogue
        localStorage.setItem('profile_industry', industry === 'Other' ? customIndustry.trim() : industry);
        
        // Also store the complete user object with client_id
        const userObject = {
          name: clientName.trim(),
          email: email.trim(),
          client_id: data.client_id || null
        };
        localStorage.setItem('user', JSON.stringify(userObject));
        
        setUser(userObject);
        setSubmissionMessage('Sign up successful! Redirecting to configure your data elements...');
        setStep(1);
        setFullName('');
        setClientName('');
        setEmail('');
        setPassword('');
        setCompanyName('');
        setIndustry('');
        setCustomIndustry('');
        setCountry('');
      }
    } catch (err) {
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
      {showToast && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          zIndex: 9999,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          pointerEvents: 'none'
        }}>
          <div style={{
            background: 'var(--success)',
            color: 'var(--success-foreground)',
            padding: '1rem 2rem',
            borderRadius: '0 0 12px 12px',
            boxShadow: 'var(--shadow-lg)',
            fontWeight: '600',
            fontSize: '1.1rem',
            pointerEvents: 'auto'
          }}>
            {submissionMessage}
          </div>
        </div>
      )}

      <div className="signup-form-mobile" style={{
        background: 'var(--card)',
        borderRadius: '1rem',
        padding: 'clamp(2rem, 5vw, 3rem)',
        width: '100%',
        maxWidth: '480px',
        boxShadow: 'var(--shadow-lg)',
        border: '1px solid var(--border)'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{
            color: 'var(--foreground)',
            fontSize: 'clamp(1.5rem, 5vw, 2rem)',
            fontWeight: '700',
            marginBottom: '0.5rem'
          }}>
            {step === 1 ? 'Create Account' : 'Company Details'}
          </h1>
          <p style={{
            color: 'var(--muted-foreground)',
            fontSize: 'clamp(0.9rem, 2.5vw, 1rem)'
          }}>
            {step === 1 ? 'Enter your personal information to get started' : 'Tell us about your company'}
          </p>
          
          {/* Step indicator */}
          <div className="signup-step-indicator" style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: '0.5rem',
            marginTop: '1.5rem'
          }}>
            <div style={{
              width: '2rem',
              height: '2rem',
              borderRadius: '50%',
              background: 'var(--primary)',
              color: 'var(--primary-foreground)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '0.9rem',
              fontWeight: '600'
            }}>
              1
            </div>
            <div style={{
              width: '3rem',
              height: '2px',
              background: step === 2 ? 'var(--primary)' : 'var(--border)'
            }} />
            <div style={{
              width: '2rem',
              height: '2rem',
              borderRadius: '50%',
              background: step === 2 ? 'var(--primary)' : 'var(--border)',
              color: step === 2 ? 'var(--primary-foreground)' : 'var(--muted-foreground)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '0.9rem',
              fontWeight: '600'
            }}>
              2
            </div>
          </div>
        </div>

        <form onSubmit={step === 1 ? handleNext : handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'clamp(1rem, 3vw, 1.5rem)' }}>
          {step === 1 ? (
            <>
              <div>
                <label htmlFor="fullName" style={{
                  display: 'block',
                  marginBottom: '0.5rem',
                  fontWeight: '500',
                  color: 'var(--foreground)'
                }}>
                  Full Name
                </label>
                <input
                  type="text"
                  id="fullName"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Enter your full name"
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
                <label htmlFor="clientName" style={{
                  display: 'block',
                  marginBottom: '0.5rem',
                  fontWeight: '500',
                  color: 'var(--foreground)'
                }}>
                  Username
                </label>
                <input
                  type="text"
                  id="clientName"
                  value={clientName}
                  onChange={(e) => setClientName(e.target.value)}
                  placeholder="Choose a username"
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
                  placeholder="Minimum 6 characters"
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
              
              <button
                type="submit"
                style={{
                  width: '100%',
                  padding: '0.875rem',
                  backgroundColor: 'var(--primary)',
                  color: 'var(--primary-foreground)',
                  border: 'none',
                  borderRadius: '0.5rem',
                  fontSize: '1rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  e.target.style.backgroundColor = 'var(--primary-hover)';
                  e.target.style.transform = 'translateY(-1px)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.backgroundColor = 'var(--primary)';
                  e.target.style.transform = 'translateY(0)';
                }}
              >
                Continue
              </button>
            </>
          ) : (
            <>
              <div>
                <label htmlFor="companyName" style={{
                  display: 'block',
                  marginBottom: '0.5rem',
                  fontWeight: '500',
                  color: 'var(--foreground)'
                }}>
                  Company Name
                </label>
                <input
                  type="text"
                  id="companyName"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="Enter your company name"
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
                <label htmlFor="industry" style={{
                  display: 'block',
                  marginBottom: '0.5rem',
                  fontWeight: '500',
                  color: 'var(--foreground)'
                }}>
                  Industry
                </label>
                <select
                  id="industry"
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.75rem 1rem',
                    border: '1px solid var(--border)',
                    borderRadius: '0.5rem',
                    fontSize: '1rem',
                    outline: 'none',
                    transition: 'border-color 0.2s ease',
                    backgroundColor: 'var(--background)',
                    color: 'var(--foreground)',
                    boxSizing: 'border-box'
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'var(--primary)'}
                  onBlur={(e) => e.target.style.borderColor = 'var(--border)'}
                >
                  <option value="">Select industry</option>
                  <option value="Health">Health</option>
                  <option value="Finance">Finance</option>
                  <option value="Restaurants">Restaurants</option>
                  <option value="Technology">Technology</option>
                  <option value="Education">Education</option>
                  <option value="Manufacturing">Manufacturing</option>
                  <option value="Retail">Retail</option>
                  <option value="Other">Other</option>
                </select>
                {industry === 'Other' && (
                  <input
                    type="text"
                    placeholder="Enter your industry"
                    value={customIndustry}
                    onChange={(e) => setCustomIndustry(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.75rem 1rem',
                      border: '1px solid var(--border)',
                      borderRadius: '0.5rem',
                      fontSize: '1rem',
                      outline: 'none',
                      transition: 'border-color 0.2s ease',
                      marginTop: '0.5rem',
                      boxSizing: 'border-box',
                      background: 'var(--background)',
                      color: 'var(--foreground)'
                    }}
                    onFocus={(e) => e.target.style.borderColor = 'var(--primary)'}
                    onBlur={(e) => e.target.style.borderColor = 'var(--border)'}
                  />
                )}
              </div>
              
              <div>
                <label htmlFor="country" style={{
                  display: 'block',
                  marginBottom: '0.5rem',
                  fontWeight: '500',
                  color: 'var(--foreground)'
                }}>
                  Country
                </label>
                <input
                  type="text"
                  id="country"
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  placeholder="Country"
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
              
              <div className="signup-buttons-mobile" style={{ display: 'flex', gap: '1rem' }}>
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  style={{
                    flex: 1,
                    padding: '0.875rem',
                    backgroundColor: 'var(--secondary)',
                    color: 'var(--secondary-foreground)',
                    border: '1px solid var(--border)',
                    borderRadius: '0.5rem',
                    fontSize: '1rem',
                    fontWeight: '500',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.backgroundColor = 'var(--muted)';
                    e.target.style.borderColor = 'var(--primary)';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.backgroundColor = 'var(--secondary)';
                    e.target.style.borderColor = 'var(--border)';
                  }}
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    flex: 1,
                    padding: '0.875rem',
                    backgroundColor: loading ? 'var(--muted)' : 'var(--primary)',
                    color: loading ? 'var(--muted-foreground)' : 'var(--primary-foreground)',
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
                  {loading ? 'Creating Account...' : 'Create Account'}
                </button>
              </div>
            </>
          )}
          
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
        </form>

        <div style={{
          textAlign: 'center',
          marginTop: '2rem',
          color: 'var(--muted-foreground)'
        }}>
          Already have an account?{' '}
          <button
            onClick={() => navigate('/login')}
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
            Log in
          </button>
        </div>
      </div>
    </div>
  );
}

export default SignupPage;
