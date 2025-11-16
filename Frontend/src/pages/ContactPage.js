import React from 'react';
import '../Css/Contact.css';
import { MapPin, Clock, Mail, Phone, Users, Linkedin, Instagram, Youtube, Github } from 'lucide-react';

// Fetch from environment variables
const companyName = process.env.REACT_APP_CONTACT_COMPANY_NAME || 'AIPlaneTech';
const address1 = process.env.REACT_APP_CONTACT_ADDRESS_LINE1 || '24 Golf Course';
const address2 = process.env.REACT_APP_CONTACT_ADDRESS_LINE2 || 'Jodhpur, Rajasthan, India';
const phone = process.env.REACT_APP_CONTACT_PHONE || '+91 78778 95426';
const email = process.env.REACT_APP_CONTACT_EMAIL || 'aiplanetech@aipglobal.in';
const linkedin = process.env.REACT_APP_CONTACT_LINKEDIN || 'https://www.linkedin.com/company/aiplanetech-pvt-ltd/';
const instagram = process.env.REACT_APP_CONTACT_INSTAGRAM || 'https://www.instagram.com/aiplanetech/';
const github = process.env.REACT_APP_CONTACT_GITHUB || 'https://github.com/AIPlaneTechIndia';
const youtube = process.env.REACT_APP_CONTACT_YOUTUBE || 'https://www.youtube.com/@AIPlaneTech-u7v';

function ContactPage() {
  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--background)',
      color: 'var(--foreground)',
      padding: '2rem',
      fontFamily: 'var(--font-family)'
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto'
      }}>
        {/* Hero Section */}
        <div style={{
          textAlign: 'center',
          marginBottom: '3rem'
        }}>
          <h1 style={{
            fontSize: 'clamp(2rem, 5vw, 3rem)',
            fontWeight: '700',
            marginBottom: '1rem',
            color: 'var(--foreground)'
          }}>
            Get in Touch with{' '}
            <span style={{
              color: 'var(--primary)',
              fontWeight: '700'
            }}>
              {companyName}
            </span>
          </h1>
          <p style={{
            fontSize: 'clamp(1rem, 2.5vw, 1.2rem)',
            color: 'var(--muted-foreground)',
            maxWidth: '600px',
            margin: '0 auto'
          }}>
            We're here to help you secure your sensitive data. Reach out to us through any of the channels below.
          </p>
        </div>

        {/* Main Content - Contact Information */}
        <div style={{
          marginBottom: '3rem'
        }}>
          <div style={{
            background: 'var(--card)',
            borderRadius: '1rem',
            padding: 'clamp(1.5rem, 4vw, 2.5rem)',
            border: '1px solid var(--border)',
            boxShadow: 'var(--shadow-lg)',
            transition: 'all 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.target.style.transform = 'translateY(-2px)';
            e.target.style.boxShadow = 'var(--shadow-glow)';
          }}
          onMouseLeave={(e) => {
            e.target.style.transform = 'translateY(0)';
            e.target.style.boxShadow = 'var(--shadow-lg)';
          }}>
            <div style={{ marginBottom: '2rem' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                marginBottom: '0.5rem'
              }}>
                <div style={{
                  background: 'var(--primary)',
                  borderRadius: '0.5rem',
                  padding: '0.5rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <MapPin size={20} style={{ color: 'var(--primary-foreground)' }} />
                </div>
                <h2 style={{
                  color: 'var(--primary)',
                  fontSize: 'clamp(1.25rem, 3vw, 1.5rem)',
                  fontWeight: '700',
                  margin: 0
                }}>
                  Contact Information
                </h2>
              </div>
              <p style={{
                color: 'var(--muted-foreground)',
                margin: 0
              }}>
                Get in touch with our team
              </p>
            </div>
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: '2rem'
            }}>
              <div>
                <h3 style={{
                  color: 'var(--foreground)',
                  fontWeight: '600',
                  marginBottom: '1.5rem'
                }}>
                  {companyName}
                </h3>
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1rem'
                }}>
                  <p style={{ color: 'var(--muted-foreground)', margin: 0 }}>{address1}</p>
                  <p style={{ color: 'var(--muted-foreground)', margin: 0 }}>{address2}</p>
                  
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    color: 'var(--muted-foreground)'
                  }}>
                    <Users size={16} />
                    <span>Air Force Area, Jodhpur</span>
                  </div>
                  
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    color: 'var(--muted-foreground)'
                  }}>
                    <Clock size={16} />
                    <span>Mon–Fri | 9:00 AM – 6:00 PM IST</span>
                  </div>
                </div>
              </div>

              <div>
                <h3 style={{
                  color: 'var(--foreground)',
                  fontWeight: '600',
                  marginBottom: '1.5rem'
                }}>
                  Contact Details
                </h3>
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1rem'
                }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    color: 'var(--muted-foreground)'
                  }}>
                    <Mail size={18} />
                    <div>
                      <div style={{ fontWeight: '500', color: 'var(--foreground)' }}>Email</div>
                      <div style={{ fontSize: '0.9rem' }}>{email}</div>
                    </div>
                  </div>
                  
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    color: 'var(--muted-foreground)'
                  }}>
                    <Phone size={18} />
                    <div>
                      <div style={{ fontWeight: '500', color: 'var(--foreground)' }}>Phone</div>
                      <div style={{ fontSize: '0.9rem' }}>{phone}</div>
                    </div>
                  </div>

                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    color: 'var(--muted-foreground)'
                  }}>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Social Media */}
        <div style={{
          background: 'var(--card)',
          borderRadius: '0.75rem',
          padding: '2rem',
          border: '1px solid var(--border)',
          boxShadow: 'var(--shadow-lg)',
          textAlign: 'center'
        }}>
          <h2 style={{
            color: 'var(--primary)',
            fontSize: '1.75rem',
            fontWeight: '700',
            marginBottom: '0.5rem'
          }}>
            Stay Connected
          </h2>
          <p style={{
            color: 'var(--muted-foreground)',
            marginBottom: '2rem'
          }}>
            Follow us for product updates, security tips, and industry insights
          </p>
          
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '1rem',
            flexWrap: 'wrap'
          }}>
            {[
              { href: linkedin, icon: Linkedin, label: 'LinkedIn' },
              { href: instagram, icon: Instagram, label: 'Instagram' },
              { href: youtube, icon: Youtube, label: 'YouTube' },
              { href: github, icon: Github, label: 'GitHub' }
            ].map(({ href, icon: Icon, label }) => (
              <a
                key={label}
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.75rem 1.5rem',
                  background: 'var(--secondary)',
                  color: 'var(--foreground)',
                  textDecoration: 'none',
                  borderRadius: '0.5rem',
                  border: '1px solid var(--border)',
                  transition: 'all 0.2s ease',
                  fontWeight: '500'
                }}
                onMouseEnter={(e) => {
                  e.target.style.backgroundColor = 'var(--primary)';
                  e.target.style.color = 'var(--primary-foreground)';
                  e.target.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.backgroundColor = 'var(--secondary)';
                  e.target.style.color = 'var(--foreground)';
                  e.target.style.transform = 'translateY(0)';
                }}
              >
                <Icon size={18} />
                {label}
              </a>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ContactPage;
