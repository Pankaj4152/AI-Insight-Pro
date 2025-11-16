import React, { useEffect, useState } from 'react';
import { API_LOGIN_URL } from '../apiConfig';
import { useNavigate } from 'react-router-dom';
import { getCurrentClientId, getCurrentUser, isComplianceOfficer } from '../utils/clientUtils';

// Add responsive styles
const responsiveStyles = `
  @media (max-width: 768px) {
    .profile-header-mobile {
      flex-direction: column !important;
      text-align: center !important;
      gap: 1rem !important;
      margin-bottom: 0.75rem !important;
    }
    
    .profile-form-mobile {
      grid-template-columns: 1fr !important;
      gap: 1.5rem !important;
    }
    
    .profile-buttons-mobile {
      flex-direction: column !important;
      gap: 0.75rem !important;
      margin-top: 1rem !important;
    }
    
    .profile-buttons-mobile button {
      width: 100% !important;
    }
  }
  
  @media (max-width: 480px) {
    .profile-container-mobile {
      padding: 0.25rem !important;
    }
    
    .profile-card-mobile {
      padding: 1rem !important;
      border-radius: 12px !important;
    }
    
    .profile-header-mobile {
      padding: 1rem !important;
      margin-bottom: 0.5rem !important;
    }
  }
`;

// Inject styles
if (typeof document !== 'undefined') {
  const styleElement = document.createElement('style');
  styleElement.textContent = responsiveStyles;
  if (!document.head.querySelector('[data-profile-responsive]')) {
    styleElement.setAttribute('data-profile-responsive', 'true');
    document.head.appendChild(styleElement);
  }
}

function ProfilePage() {
  const [profile, setProfile] = useState({
    full_name: '',
    username: '',
    email: '',
    company_name: '',
    industry: '',
    country: '',
  });

  const [complianceProfile, setComplianceProfile] = useState(null);
  const [originalProfile, setOriginalProfile] = useState(null);
  const [customIndustry, setCustomIndustry] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const navigate = useNavigate();

  const currentUser = getCurrentUser();
  const isCompliance = isComplianceOfficer();
  const selectedClientId = getCurrentClientId(); // This is the selected client from dropdown
  const complianceOfficerId = currentUser.client_id; // This is the compliance officer's own ID

  // Industry options
  const industryOptions = [
    { value: "Health", label: "Health" },
    { value: "Finance", label: "Finance" },
    { value: "Restaurants", label: "Restaurants" },
    { value: "Other", label: "Other" },
  ];

  useEffect(() => {
    const fetchProfiles = async () => {
      if (isCompliance) {
        // For compliance officers, fetch both their own profile and the selected client's profile
        try {
          // Fetch compliance officer's own profile
          if (complianceOfficerId) {
            const complianceRes = await fetch(`${API_LOGIN_URL}/get-profile?client_id=${complianceOfficerId}`);
            const complianceData = await complianceRes.json();
            if (complianceRes.ok) {
              setComplianceProfile(complianceData);
            }
          }

          // Fetch selected client's profile
          if (selectedClientId) {
            const clientRes = await fetch(`${API_LOGIN_URL}/get-profile?client_id=${selectedClientId}`);
            const clientData = await clientRes.json();
            if (clientRes.ok) {
              setProfile(clientData);
              setOriginalProfile(clientData);
            } else {
              setError(clientData.detail || 'Failed to load selected client profile.');
            }
          } else {
            setError('No client selected. Please select a client from the dropdown.');
          }
        } catch (err) {
          setError('An error occurred while fetching profiles.');
        }
      } else {
        // For regular users, fetch their own profile
        if (!selectedClientId) {
          setError('User not found. Please log in again.');
          return;
        }
        try {
          const res = await fetch(`${API_LOGIN_URL}/get-profile?client_id=${selectedClientId}`);
          const data = await res.json();
          if (res.ok) {
            setProfile(data);
            setOriginalProfile(data);

            // Store in localStorage
            localStorage.setItem('profile_full_name', data.full_name || '');
            localStorage.setItem('profile_username', data.username || '');
            localStorage.setItem('profile_email', data.email || '');
            localStorage.setItem('profile_company_name', data.company_name || '');
            localStorage.setItem('profile_industry', data.industry || '');
            localStorage.setItem('profile_country', data.country || '');
          } else {
            setError(data.detail || 'Failed to load profile.');
          }
        } catch (err) {
          setError('An error occurred while fetching your profile.');
        }
      }
    };

    fetchProfiles();
  }, [selectedClientId, complianceOfficerId, isCompliance]);

  const handleChange = (e) => {
    setProfile({ ...profile, [e.target.name]: e.target.value });
  };

  const handleCustomIndustryChange = (e) => {
    setCustomIndustry(e.target.value);
  };

  const handleCancel = () => {
    setProfile(originalProfile);
    setCustomIndustry('');
    setIsEditing(false);
    setMessage('');
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setError('');

    const updatedProfile = {
      ...profile,
      industry: profile.industry === 'Other' ? customIndustry : profile.industry,
      client_id: selectedClientId,
    };

    try {
      const res = await fetch(`${API_LOGIN_URL}/update-profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedProfile),
      });

      const data = await res.json();
      if (res.ok) {
        setMessage('Profile updated successfully!');
        setOriginalProfile(updatedProfile);
        setIsEditing(false);
        localStorage.setItem('userIndustry', updatedProfile.industry); // Store industry in localStorage
      } else {
        setError(data.detail || 'Failed to update profile.');
      }
    } catch {
      setError('A network error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--background)',
      color: 'var(--foreground)',
      padding: '1rem 1rem 0 1rem',
      fontFamily: 'var(--font-family)'
    }}>
      <div className="profile-container-mobile" style={{
        maxWidth: '1000px',
        margin: '0 auto',
        padding: '0 0.5rem 0 0.5rem'
      }}>
        {/* Compliance Officer Profile Section */}
        {isCompliance && complianceProfile && (
          <div style={{
            background: 'var(--card)',
            padding: '1.5rem',
            borderRadius: '20px',
            marginBottom: '1rem',
            border: '2px solid #3B82F6',
            boxShadow: 'var(--shadow-lg)'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '1rem',
              marginBottom: '1rem'
            }}>
              <div style={{
                width: '48px',
                height: '48px',
                background: '#3B82F6',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white'
              }}>
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6m2-3a2 2 0 1 1-4 0 2 2 0 0 1 4 0m4 8c0 1-1 1-1 1H3s-1 0-1-1 1-4 6-4 6 3 6 4"/>
                </svg>
              </div>
              <div>
                <h2 style={{ margin: 0, color: '#3B82F6', fontSize: '1.5rem' }}>
                  Compliance Officer Profile
                </h2>
                <p style={{ margin: 0, color: 'var(--muted-foreground)', fontSize: '0.9rem' }}>
                  Your compliance officer account information
                </p>
              </div>
            </div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '1rem',
              padding: '1rem',
              background: 'var(--muted)',
              borderRadius: '12px'
            }}>
              <div>
                <strong>Name:</strong> {complianceProfile.full_name}
              </div>
              <div>
                <strong>Username:</strong> {complianceProfile.username}
              </div>
              <div>
                <strong>Email:</strong> {complianceProfile.email}
              </div>
              <div>
                <strong>Company:</strong> {complianceProfile.company_name}
              </div>
              <div>
                <strong>Role:</strong> {complianceProfile.role || 'Compliance Officer'}
              </div>
            </div>
          </div>
        )}

        {/* Selected Client Profile Header */}
        {isCompliance && (
          <div style={{
            background: 'var(--muted)',
            padding: '1rem',
            borderRadius: '12px',
            marginBottom: '1rem',
            textAlign: 'center'
          }}>
            <h3 style={{ margin: 0, color: 'var(--foreground)' }}>
              Selected Client Profile
            </h3>
            <p style={{ margin: '0.5rem 0 0 0', color: 'var(--muted-foreground)', fontSize: '0.9rem' }}>
              You are viewing and can edit the profile of the selected client
            </p>
          </div>
        )}

        {/* Profile Header */}
        <div className="profile-header-mobile" style={{
          background: 'var(--card)',
          padding: '1.5rem',
          borderRadius: '20px',
          marginBottom: '1rem',
          border: '1px solid var(--border)',
          boxShadow: 'var(--shadow-lg)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            flex: '1',
            minWidth: '280px'
          }}>
            <div style={{
              width: '64px',
              height: '64px',
              background: 'var(--primary-gradient)',
              borderRadius: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--primary-foreground)',
              flexShrink: '0'
            }}>
              <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" fill="currentColor" viewBox="0 0 16 16">
                <path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6m2-3a2 2 0 1 1-4 0 2 2 0 0 1 4 0m4 8c0 1-1 1-1 1H3s-1 0-1-1 1-4 6-4 6 3 6 4m-1-.004c-.001-.246-.154-.986-.832-1.664C11.516 10.68 10.289 10 8 10s-3.516.68-4.168 1.332c-.678.678-.83 1.418-.832 1.664z"/>
              </svg>
            </div>
            <div>
              <h1 style={{
                fontSize: 'clamp(1.25rem, 4vw, 2rem)',
                fontWeight: '700',
                color: 'var(--foreground)',
                margin: '0 0 0.25rem 0',
                lineHeight: '1.2'
              }}>{profile.full_name || 'Your Profile'}</h1>
              <p style={{
                fontSize: 'clamp(0.875rem, 3vw, 1.125rem)',
                color: 'var(--muted-foreground)',
                margin: '0 0 0.25rem 0',
                wordBreak: 'break-word'
              }}>{profile.email}</p>
              {profile.company_name && (
                <p style={{
                  fontSize: 'clamp(0.8rem, 2.5vw, 1rem)',
                  color: 'var(--primary)',
                  margin: 0,
                  fontWeight: '600',
                  wordBreak: 'break-word'
                }}>{profile.company_name}</p>
              )}
            </div>
          </div>
          <div>
            {!isEditing && (
              <button 
                type="button" 
                onClick={() => setIsEditing(true)}
                style={{
                  padding: '0.75rem 1.5rem',
                  background: 'var(--primary-gradient)',
                  color: 'var(--primary-foreground)',
                  border: 'none',
                  borderRadius: '12px',
                  fontWeight: '600',
                  fontSize: 'clamp(0.875rem, 2.5vw, 1rem)',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  boxShadow: 'var(--shadow-md)',
                  whiteSpace: 'nowrap'
                }}
                onMouseOver={(e) => e.target.style.transform = 'translateY(-2px)'}
                onMouseOut={(e) => e.target.style.transform = 'translateY(0)'}
              >
                Edit Profile
              </button>
            )}
          </div>
        </div>

        {/* Messages */}
        {message && (
          <div style={{
            background: 'var(--success)',
            color: 'var(--success-foreground)',
            padding: '1rem 1.5rem',
            borderRadius: '12px',
            marginBottom: '1rem',
            textAlign: 'center',
            boxShadow: 'var(--shadow-md)'
          }}>
            {message}
          </div>
        )}
        {error && (
          <div style={{
            background: 'var(--destructive)',
            color: 'var(--destructive-foreground)',
            padding: '1rem 1.5rem',
            borderRadius: '12px',
            marginBottom: '1rem',
            textAlign: 'center',
            boxShadow: 'var(--shadow-md)'
          }}>
            {error}
          </div>
        )}

        {/* Form Structure */}
        <div className="profile-card-mobile" style={{
          background: 'var(--card)',
          padding: 'clamp(1.5rem, 4vw, 2.5rem)',
          borderRadius: '20px',
          border: '1px solid var(--border)',
          boxShadow: 'var(--shadow-lg)'
        }}>
          <form id="profileForm" onSubmit={handleSubmit}>
            <div className="profile-form-mobile" style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
              gap: 'clamp(2rem, 5vw, 3rem)' 
            }}>
              {/* Left Column */}
              <div>
                <h2 style={{
                  fontSize: '1.5rem',
                  fontWeight: '700',
                  color: 'var(--foreground)',
                  marginBottom: '1.5rem',
                  paddingBottom: '0.5rem',
                  borderBottom: '2px solid var(--border)'
                }}>Account Info</h2>
                
                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    color: 'var(--foreground)',
                    marginBottom: '0.5rem'
                  }}>Full Name</label>
                  <input 
                    type="text" 
                    id="full_name" 
                    name="full_name" 
                    value={profile.full_name} 
                    onChange={handleChange} 
                    disabled={!isEditing}
                    style={{
                      width: '100%',
                      padding: '0.75rem 1rem',
                      border: isEditing ? '2px solid var(--border)' : '2px solid var(--muted)',
                      borderRadius: '12px',
                      fontSize: '1rem',
                      outline: 'none',
                      transition: 'all 0.2s',
                      background: isEditing ? 'var(--background)' : 'var(--muted)',
                      color: isEditing ? 'var(--foreground)' : 'var(--muted-foreground)',
                      boxSizing: 'border-box'
                    }}
                    onFocus={(e) => isEditing && (e.target.style.borderColor = 'var(--primary)')}
                    onBlur={(e) => isEditing && (e.target.style.borderColor = 'var(--border)')}
                  />
                </div>
                
                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    color: 'var(--foreground)',
                    marginBottom: '0.5rem'
                  }}>Username</label>
                  <input 
                    type="text" 
                    id="username" 
                    name="username" 
                    value={profile.username} 
                    onChange={handleChange} 
                    disabled={!isEditing}
                    style={{
                      width: '100%',
                      padding: '0.75rem 1rem',
                      border: isEditing ? '2px solid var(--border)' : '2px solid var(--muted)',
                      borderRadius: '12px',
                      fontSize: '1rem',
                      outline: 'none',
                      transition: 'all 0.2s',
                      background: isEditing ? 'var(--background)' : 'var(--muted)',
                      color: isEditing ? 'var(--foreground)' : 'var(--muted-foreground)',
                      boxSizing: 'border-box'
                    }}
                    onFocus={(e) => isEditing && (e.target.style.borderColor = 'var(--primary)')}
                    onBlur={(e) => isEditing && (e.target.style.borderColor = 'var(--border)')}
                  />
                </div>
                
                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    color: 'var(--foreground)',
                    marginBottom: '0.5rem'
                  }}>Email</label>
                  <input 
                    type="email" 
                    id="email" 
                    name="email" 
                    value={profile.email} 
                    onChange={handleChange} 
                    disabled={!isEditing}
                    style={{
                      width: '100%',
                      padding: '0.75rem 1rem',
                      border: isEditing ? '2px solid var(--border)' : '2px solid var(--muted)',
                      borderRadius: '12px',
                      fontSize: '1rem',
                      outline: 'none',
                      transition: 'all 0.2s',
                      background: isEditing ? 'var(--background)' : 'var(--muted)',
                      color: isEditing ? 'var(--foreground)' : 'var(--muted-foreground)',
                      boxSizing: 'border-box'
                    }}
                    onFocus={(e) => isEditing && (e.target.style.borderColor = 'var(--primary)')}
                    onBlur={(e) => isEditing && (e.target.style.borderColor = 'var(--border)')}
                  />
                </div>
              </div>

              {/* Right Column */}
              <div>
                <h2 style={{
                  fontSize: '1.5rem',
                  fontWeight: '700',
                  color: 'var(--foreground)',
                  marginBottom: '1.5rem',
                  paddingBottom: '0.5rem',
                  borderBottom: '2px solid var(--border)'
                }}>Company Info</h2>
                
                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    color: 'var(--foreground)',
                    marginBottom: '0.5rem'
                  }}>Company Name</label>
                  <input 
                    type="text" 
                    id="company_name" 
                    name="company_name" 
                    value={profile.company_name} 
                    onChange={handleChange} 
                    disabled={!isEditing}
                    style={{
                      width: '100%',
                      padding: '0.75rem 1rem',
                      border: isEditing ? '2px solid var(--border)' : '2px solid var(--muted)',
                      borderRadius: '12px',
                      fontSize: '1rem',
                      outline: 'none',
                      transition: 'all 0.2s',
                      background: isEditing ? 'var(--background)' : 'var(--muted)',
                      color: isEditing ? 'var(--foreground)' : 'var(--muted-foreground)',
                      boxSizing: 'border-box'
                    }}
                    onFocus={(e) => isEditing && (e.target.style.borderColor = 'var(--primary)')}
                    onBlur={(e) => isEditing && (e.target.style.borderColor = 'var(--border)')}
                  />
                </div>
                
                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    color: 'var(--foreground)',
                    marginBottom: '0.5rem'
                  }}>Industry</label>
                  <select 
                    id="industry" 
                    name="industry" 
                    value={profile.industry} 
                    onChange={handleChange} 
                    disabled={!isEditing}
                    style={{
                      width: '100%',
                      padding: '0.75rem 1rem',
                      border: isEditing ? '2px solid var(--border)' : '2px solid var(--muted)',
                      borderRadius: '12px',
                      fontSize: '1rem',
                      outline: 'none',
                      transition: 'all 0.2s',
                      background: isEditing ? 'var(--background)' : 'var(--muted)',
                      color: isEditing ? 'var(--foreground)' : 'var(--muted-foreground)',
                      boxSizing: 'border-box'
                    }}
                    onFocus={(e) => isEditing && (e.target.style.borderColor = 'var(--primary)')}
                    onBlur={(e) => isEditing && (e.target.style.borderColor = 'var(--border)')}
                  >
                    <option value="">Select an industry</option>
                    {industryOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                {profile.industry === 'Other' && (
                  <div style={{ marginBottom: '1.5rem' }}>
                    <label style={{
                      display: 'block',
                      fontSize: '0.875rem',
                      fontWeight: '600',
                      color: 'var(--foreground)',
                      marginBottom: '0.5rem'
                    }}>Custom Industry</label>
                    <input 
                      type="text" 
                      id="customIndustry" 
                      name="customIndustry" 
                      value={customIndustry} 
                      onChange={handleCustomIndustryChange} 
                      disabled={!isEditing}
                      placeholder="Enter your industry"
                      style={{
                        width: '100%',
                        padding: '0.75rem 1rem',
                        border: isEditing ? '2px solid var(--border)' : '2px solid var(--muted)',
                        borderRadius: '12px',
                        fontSize: '1rem',
                        outline: 'none',
                        transition: 'all 0.2s',
                        background: isEditing ? 'var(--background)' : 'var(--muted)',
                        color: isEditing ? 'var(--foreground)' : 'var(--muted-foreground)',
                        boxSizing: 'border-box'
                      }}
                      onFocus={(e) => isEditing && (e.target.style.borderColor = 'var(--primary)')}
                      onBlur={(e) => isEditing && (e.target.style.borderColor = 'var(--border)')}
                    />
                  </div>
                )}
                
                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    color: 'var(--foreground)',
                    marginBottom: '0.5rem'
                  }}>Country</label>
                  <input 
                    type="text" 
                    id="country" 
                    name="country" 
                    value={profile.country} 
                    onChange={handleChange} 
                    disabled={!isEditing}
                    style={{
                      width: '100%',
                      padding: '0.75rem 1rem',
                      border: isEditing ? '2px solid var(--border)' : '2px solid var(--muted)',
                      borderRadius: '12px',
                      fontSize: '1rem',
                      outline: 'none',
                      transition: 'all 0.2s',
                      background: isEditing ? 'var(--background)' : 'var(--muted)',
                      color: isEditing ? 'var(--foreground)' : 'var(--muted-foreground)',
                      boxSizing: 'border-box'
                    }}
                    onFocus={(e) => isEditing && (e.target.style.borderColor = 'var(--primary)')}
                    onBlur={(e) => isEditing && (e.target.style.borderColor = 'var(--border)')}
                  />
                </div>
              </div>
            </div>
          </form>

          {/* Action Buttons */}
          {isEditing && (
            <div className="profile-buttons-mobile" style={{ 
              marginTop: '1.5rem', 
              display: 'flex', 
              gap: '1rem', 
              justifyContent: 'center',
              flexWrap: 'wrap'
            }}>
              <button 
                type="button" 
                onClick={handleCancel}
                style={{
                  padding: '0.875rem 2rem',
                  background: 'var(--muted)',
                  color: 'var(--muted-foreground)',
                  border: '1px solid var(--border)',
                  borderRadius: '12px',
                  fontWeight: '600',
                  fontSize: '1rem',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  boxShadow: 'var(--shadow-md)'
                }}
                onMouseOver={(e) => {
                  e.target.style.transform = 'translateY(-2px)';
                  e.target.style.background = 'var(--secondary)';
                }}
                onMouseOut={(e) => {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.background = 'var(--muted)';
                }}
              >
                Cancel
              </button>
              <button 
                type="submit" 
                form="profileForm" 
                disabled={loading}
                style={{
                  padding: '0.875rem 2rem',
                  background: loading ? 'var(--muted)' : 'var(--primary-gradient)',
                  color: loading ? 'var(--muted-foreground)' : 'var(--primary-foreground)',
                  border: 'none',
                  borderRadius: '12px',
                  fontWeight: '600',
                  fontSize: '1rem',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  transition: 'all 0.2s',
                  boxShadow: 'var(--shadow-md)'
                }}
                onMouseOver={(e) => !loading && (e.target.style.transform = 'translateY(-2px)')}
                onMouseOut={(e) => !loading && (e.target.style.transform = 'translateY(0)')}
              >
                {loading ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ProfilePage;