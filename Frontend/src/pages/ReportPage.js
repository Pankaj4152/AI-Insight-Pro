import React, { useState, useEffect } from 'react';
import { FileText, Download, Eye, Building, User, Mail, AlertCircle, CheckCircle2 } from 'lucide-react';
import { API_BASE_URL, API_LOGIN_URL } from '../apiConfig';
import { getCurrentClientId } from '../utils/clientUtils';

const Report = ({ theme }) => {
  const [selectedFormat, setSelectedFormat] = useState('pdf');
  const [showPreview, setShowPreview] = useState(false);
  const [clientId, setClientId] = useState('');
  const [userName, setUserName] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [company, setCompany] = useState('');
  const [htmlPreview, setHtmlPreview] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    // Fetch client_id from localStorage
    const cid = getCurrentClientId() || '';
    setClientId(cid);
    if (cid) {
      // Fetch profile from API_LOGIN_URL
      fetch(`${API_LOGIN_URL}/get-profile?client_id=${cid}`)
        .then(res => res.json())
        .then(data => {
          setUserName(data.full_name || '');
          setUserEmail(data.email || '');
          setCompany(data.company_name || '');
        })
        .catch(() => {
          setUserName('');
          setUserEmail('');
          setCompany('');
        });
    }
  }, []);

  // Download or preview report from backend
  const handleReportDownload = async () => {
    setError('');
    setHtmlPreview('');
    if (!clientId) {
      setError('Please enter a client ID.');
      return;
    }
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/risk/report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: clientId,
          format: selectedFormat,
          name: userName,
          email: userEmail,
          company: company
        })
      });
      if (!response.ok) {
        const err = await response.json();
        setError(err.message || 'Failed to fetch report.');
        setLoading(false);
        return;
      }
      if (selectedFormat === 'html') {
        const html = await response.text();
        setHtmlPreview(html);
        setShowPreview(true);
      } else {
        // PDF or LaTeX: download as file
        const blob = await response.blob();
        const extension = selectedFormat === 'pdf' ? 'pdf' : 'tex';
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        // Use profile name for filename, fallback to client ID if no name
        const fileName = userName ? `risk_report_${userName.replace(/[^a-zA-Z0-9]/g, '_')}` : `risk_report_${clientId}`;
        a.download = `${fileName}.${extension}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      }
    } catch (err) {
      setError('Error fetching report.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--background)',
      color: 'var(--foreground)',
      padding: '2rem 1rem',
      fontFamily: 'var(--font-family)'
    }}>
      <div style={{
        maxWidth: '900px',
        margin: '0 auto'
      }}>
        {/* Header */}
        <div style={{
          background: 'var(--card)',
          borderRadius: '1.5rem',
          padding: '3rem',
          marginBottom: '2rem',
          boxShadow: 'var(--shadow-lg)',
          border: '1px solid var(--border)'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            marginBottom: '2rem'
          }}>
            <div style={{
              width: '60px',
              height: '60px',
              borderRadius: '1rem',
              background: 'var(--primary-gradient)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--primary-foreground)'
            }}>
              <FileText size={28} />
            </div>
            <div>
              <h1 style={{
                fontSize: '2.5rem',
                fontWeight: '800',
                color: 'var(--foreground)',
                margin: 0,
                lineHeight: '1.1'
              }}>
                Risk Assessment{' '}
                <span style={{
                  color: 'var(--primary)',
                  fontWeight: '800'
                }}>
                  Report
                </span>
              </h1>
              <p style={{
                color: 'var(--muted-foreground)',
                fontSize: '1.1rem',
                margin: '0.5rem 0 0 0'
              }}>
                Generate comprehensive risk assessment reports for your organization
              </p>
            </div>
          </div>

          {/* Profile Information */}
          {(company || userName) && (
            <div style={{
              background: 'var(--secondary)',
              borderRadius: '1rem',
              padding: '1.5rem',
              border: '1px solid var(--border)'
            }}>
              <h3 style={{
                fontSize: '1.2rem',
                fontWeight: '600',
                color: 'var(--foreground)',
                marginBottom: '1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <User size={20} />
                Profile Information
              </h3>
              <div style={{
                display: 'grid',
                gap: '0.75rem'
              }}>
                {company && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    color: 'var(--muted-foreground)'
                  }}>
                    <Building size={18} />
                    <span style={{ fontWeight: '500' }}>Company:</span>
                    <span style={{ fontWeight: '600', color: 'var(--foreground)' }}>{company}</span>
                  </div>
                )}
                {userName && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    color: 'var(--muted-foreground)'
                  }}>
                    <User size={18} />
                    <span style={{ fontWeight: '500' }}>Name:</span>
                    <span style={{ fontWeight: '600', color: 'var(--foreground)' }}>{userName}</span>
                  </div>
                )}
                {userEmail && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    color: 'var(--muted-foreground)'
                  }}>
                    <Mail size={18} />
                    <span style={{ fontWeight: '500' }}>Email:</span>
                    <span style={{ fontWeight: '600', color: 'var(--foreground)' }}>{userEmail}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Report Generation */}
        <div style={{
          background: 'var(--card)',
          borderRadius: '1.5rem',
          padding: '2.5rem',
          boxShadow: 'var(--shadow-lg)',
          border: '1px solid var(--border)'
        }}>
          <h3 style={{
            fontSize: '1.5rem',
            fontWeight: '700',
            color: 'var(--foreground)',
            marginBottom: '1.5rem'
          }}>
            Generate Report
          </h3>

          <div style={{
            display: 'flex',
            gap: '1rem',
            alignItems: 'flex-end',
            flexWrap: 'wrap'
          }}>
            <div style={{
              flex: '1',
              minWidth: '200px'
            }}>
              <label style={{
                display: 'block',
                fontSize: '0.9rem',
                fontWeight: '600',
                color: 'var(--foreground)',
                marginBottom: '0.5rem'
              }}>
                Report Format
              </label>
              <select
                value={selectedFormat}
                onChange={(e) => setSelectedFormat(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.875rem 1rem',
                  borderRadius: '0.75rem',
                  border: '2px solid var(--border)',
                  fontSize: '1rem',
                  background: 'var(--background)',
                  color: 'var(--foreground)',
                  outline: 'none',
                  transition: 'all 0.2s ease'
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = 'var(--primary)';
                  e.target.style.boxShadow = '0 0 0 3px var(--ring) / 0.1';
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = 'var(--border)';
                  e.target.style.boxShadow = 'none';
                }}
              >
                <option value="pdf">PDF Document</option>
                <option value="html">HTML Preview</option>
              </select>
            </div>

            <button
              onClick={handleReportDownload}
              disabled={loading}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.875rem 2rem',
                background: loading ? 'var(--muted)' : 'var(--primary-gradient)',
                color: loading ? 'var(--muted-foreground)' : 'var(--primary-foreground)',
                border: 'none',
                borderRadius: '0.75rem',
                fontSize: '1rem',
                fontWeight: '600',
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'all 0.3s ease',
                minWidth: '150px',
                justifyContent: 'center'
              }}
              onMouseEnter={(e) => {
                if (!loading) {
                  e.target.style.transform = 'translateY(-2px)';
                  e.target.style.boxShadow = 'var(--shadow-glow)';
                }
              }}
              onMouseLeave={(e) => {
                if (!loading) {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = 'none';
                }
              }}
            >
              {loading ? (
                <>
                  <div style={{
                    width: '18px',
                    height: '18px',
                    border: '2px solid transparent',
                    borderTop: '2px solid currentColor',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }} />
                  Loading...
                </>
              ) : (
                <>
                  {selectedFormat === 'html' ? <Eye size={18} /> : <Download size={18} />}
                  {selectedFormat === 'html' ? 'Preview' : 'Download'}
                </>
              )}
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div style={{
              marginTop: '1.5rem',
              padding: '1rem',
              background: 'var(--destructive)',
              border: '1px solid var(--destructive)',
              borderRadius: '0.75rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              color: 'var(--destructive-foreground)'
            }}>
              <AlertCircle size={20} />
              <span style={{ fontWeight: '500' }}>{error}</span>
            </div>
          )}
        </div>

        {/* HTML Preview */}
        {showPreview && selectedFormat === 'html' && htmlPreview && (
          <div style={{
            marginTop: '2rem',
            background: 'var(--card)',
            borderRadius: '1.5rem',
            overflow: 'hidden',
            boxShadow: 'var(--shadow-lg)',
            border: '1px solid var(--border)'
          }}>
            <div style={{
              padding: '1.5rem',
              background: 'var(--secondary)',
              borderBottom: '1px solid var(--border)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem'
            }}>
              <CheckCircle2 size={20} style={{ color: 'var(--success)' }} />
              <span style={{
                fontWeight: '600',
                color: 'var(--foreground)'
              }}>
                Report Preview
              </span>
            </div>
            <div
              style={{
                padding: '2rem',
                maxHeight: '600px',
                overflow: 'auto'
              }}
              dangerouslySetInnerHTML={{ __html: htmlPreview }}
            />
          </div>
        )}
      </div>

      {/* CSS Animation for loading spinner */}
      <style jsx>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default Report;
