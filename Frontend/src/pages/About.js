import React from 'react';
import { Link } from 'react-router-dom';
import { Users, Target, Award, Shield, Zap, Globe } from 'lucide-react';

const About = () => {
  return (
    <div style={{
      minHeight: '100vh',
      background: 'hsl(0 0% 100%)',
      padding: '2rem 1rem'
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto'
      }}>
        {/* Hero Section */}
        <div style={{
          textAlign: 'center',
          marginBottom: '4rem'
        }}>
          <h1 className="page-title">
            About AIPlaneTech
          </h1>
          <p style={{
            fontSize: '1.5rem',
            color: 'hsl(215.4 16.3% 46.9%)',
            margin: 0,
            maxWidth: '800px',
            marginLeft: 'auto',
            marginRight: 'auto',
            lineHeight: '1.6'
          }}>
            Pioneering AI-Powered Data Protection and Risk Assessment Solutions
          </p>
        </div>

        {/* Mission Section */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          padding: '3rem',
          borderRadius: '20px',
          marginBottom: '2rem',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            marginBottom: '1.5rem'
          }}>
            <div style={{
              width: '60px',
              height: '60px',
              background: 'linear-gradient(135deg, hsl(198 88% 32%), hsl(172 76% 47%))',
              borderRadius: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginRight: '1rem'
            }}>
              <Target size={30} color="white" />
            </div>
            <h2 style={{
              fontSize: '2.25rem',
              fontWeight: '700',
              color: '#1f2937',
              margin: 0
            }}>Our Mission</h2>
          </div>
          <p style={{
            fontSize: '1.125rem',
            color: '#6b7280',
            lineHeight: '1.8',
            margin: 0
          }}>
            At AIPlaneTech, we're committed to revolutionizing data protection through 
            cutting-edge AI technology. Our mission is to empower organizations with 
            intelligent, automated risk assessment and compliance solutions that protect 
            sensitive data while enabling business growth.
          </p>
        </div>

        {/* Vision Section */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          padding: '3rem',
          borderRadius: '20px',
          marginBottom: '2rem',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            marginBottom: '1.5rem'
          }}>
            <div style={{
              width: '60px',
              height: '60px',
              background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)',
              borderRadius: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginRight: '1rem'
            }}>
              <Globe size={30} color="white" />
            </div>
            <h2 style={{
              fontSize: '2.25rem',
              fontWeight: '700',
              color: '#1f2937',
              margin: 0
            }}>Our Vision</h2>
          </div>
          <p style={{
            fontSize: '1.125rem',
            color: '#6b7280',
            lineHeight: '1.8',
            margin: 0
          }}>
            We envision a world where data security is seamless, intelligent, and 
            accessible to all organizations. Through AI-Insight-Pro, we're building 
            the future of data protection—one where advanced analytics and machine 
            learning work together to create impenetrable digital fortresses.
          </p>
        </div>

        {/* Values Section */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          padding: '3rem',
          borderRadius: '20px',
          marginBottom: '2rem',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            marginBottom: '2rem'
          }}>
            <div style={{
              width: '60px',
              height: '60px',
              background: 'linear-gradient(135deg, #f59e0b 0%, #ea580c 100%)',
              borderRadius: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginRight: '1rem'
            }}>
              <Award size={30} color="white" />
            </div>
            <h2 style={{
              fontSize: '2.25rem',
              fontWeight: '700',
              color: '#1f2937',
              margin: 0
            }}>Our Values</h2>
          </div>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '2rem'
          }}>
            <div style={{
              background: 'white',
              padding: '2rem',
              borderRadius: '16px',
              textAlign: 'center',
              border: '1px solid #e5e7eb',
              transition: 'all 0.3s',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }}>
              <div style={{
                width: '50px',
                height: '50px',
                background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 1rem'
              }}>
                <Shield size={24} color="white" />
              </div>
              <h3 style={{
                fontSize: '1.25rem',
                fontWeight: '600',
                color: '#1f2937',
                marginBottom: '0.75rem'
              }}>Security First</h3>
              <p style={{
                color: '#6b7280',
                margin: 0,
                lineHeight: '1.6'
              }}>
                Every solution we build prioritizes the protection of your most valuable assets.
              </p>
            </div>
            
            <div style={{
              background: 'white',
              padding: '2rem',
              borderRadius: '16px',
              textAlign: 'center',
              border: '1px solid #e5e7eb',
              transition: 'all 0.3s',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }}>
              <div style={{
                width: '50px',
                height: '50px',
                background: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 1rem'
              }}>
                <Zap size={24} color="white" />
              </div>
              <h3 style={{
                fontSize: '1.25rem',
                fontWeight: '600',
                color: '#1f2937',
                marginBottom: '0.75rem'
              }}>Innovation</h3>
              <p style={{
                color: '#6b7280',
                margin: 0,
                lineHeight: '1.6'
              }}>
                We constantly push the boundaries of what's possible with AI and data protection.
              </p>
            </div>
            
            <div style={{
              background: 'white',
              padding: '2rem',
              borderRadius: '16px',
              textAlign: 'center',
              border: '1px solid #e5e7eb',
              transition: 'all 0.3s',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }}>
              <div style={{
                width: '50px',
                height: '50px',
                background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 1rem'
              }}>
                <Users size={24} color="white" />
              </div>
              <h3 style={{
                fontSize: '1.25rem',
                fontWeight: '600',
                color: '#1f2937',
                marginBottom: '0.75rem'
              }}>Customer Success</h3>
              <p style={{
                color: '#6b7280',
                margin: 0,
                lineHeight: '1.6'
              }}>
                Your success is our success. We're here to support you every step of the way.
              </p>
            </div>
          </div>
        </div>

        {/* Team and Technology Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))',
          gap: '2rem',
          marginBottom: '2rem'
        }}>
          {/* Team Section */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
            padding: '3rem',
            borderRadius: '20px',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: '1.5rem'
            }}>
              <div style={{
                width: '50px',
                height: '50px',
                background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginRight: '1rem'
              }}>
                <Users size={24} color="white" />
              </div>
              <h2 style={{
                fontSize: '1.875rem',
                fontWeight: '700',
                color: '#1f2937',
                margin: 0
              }}>Our Team</h2>
            </div>
            <p style={{
              fontSize: '1.125rem',
              color: '#6b7280',
              lineHeight: '1.8',
              margin: 0
            }}>
              Our team consists of cybersecurity experts, AI specialists, and data scientists 
              who are passionate about creating innovative solutions that protect businesses 
              in the digital age. Based in Jodhpur, Rajasthan, we bring together local 
              talent with global expertise.
            </p>
          </div>

          {/* Technology Section */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
            padding: '3rem',
            borderRadius: '20px',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: '1.5rem'
            }}>
              <div style={{
                width: '50px',
                height: '50px',
                background: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginRight: '1rem'
              }}>
                <Zap size={24} color="white" />
              </div>
              <h2 style={{
                fontSize: '1.875rem',
                fontWeight: '700',
                color: '#1f2937',
                margin: 0
              }}>Our Technology</h2>
            </div>
            <p style={{
              fontSize: '1.125rem',
              color: '#6b7280',
              lineHeight: '1.8',
              margin: 0
            }}>
              AI-Insight-Pro leverages state-of-the-art artificial intelligence and machine 
              learning algorithms to provide real-time risk assessment, automated compliance 
              monitoring, and intelligent data protection. Our platform continuously learns 
              and adapts to new threats, ensuring your data remains secure.
            </p>
          </div>
        </div>

        {/* Contact Section */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          padding: '3rem',
          borderRadius: '20px',
          textAlign: 'center',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '1.5rem'
          }}>
            <div style={{
              width: '60px',
              height: '60px',
              background: 'linear-gradient(135deg, #f59e0b 0%, #ea580c 100%)',
              borderRadius: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginRight: '1rem'
            }}>
              <Globe size={30} color="white" />
            </div>
            <h2 style={{
              fontSize: '2.25rem',
              fontWeight: '700',
              color: '#1f2937',
              margin: 0
            }}>Get in Touch</h2>
          </div>
          <p style={{
            fontSize: '1.125rem',
            color: '#6b7280',
            lineHeight: '1.8',
            marginBottom: '2rem',
            maxWidth: '600px',
            marginLeft: 'auto',
            marginRight: 'auto'
          }}>
            Ready to transform your data protection strategy? Contact our team to learn 
            how AI-Insight-Pro can help secure your organization's future.
          </p>
          <div style={{
            display: 'flex',
            gap: '1rem',
            justifyContent: 'center',
            flexWrap: 'wrap'
          }}>
            <Link 
              to="/contact" 
              style={{
                display: 'inline-block',
                padding: '1rem 2rem',
                background: 'linear-gradient(135deg, hsl(198 88% 32%), hsl(172 76% 47%))',
                color: 'white',
                textDecoration: 'none',
                borderRadius: '12px',
                fontWeight: '600',
                fontSize: '1.1rem',
                transition: 'all 0.2s',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
              onMouseOver={(e) => e.target.style.transform = 'translateY(-2px)'}
              onMouseOut={(e) => e.target.style.transform = 'translateY(0)'}
            >
              Contact Us
            </Link>
            <Link 
              to="/home" 
              style={{
                display: 'inline-block',
                padding: '1rem 2rem',
                background: 'hsl(0 0% 100%)',
                color: 'hsl(222.2 84% 4.9%)',
                textDecoration: 'none',
                borderRadius: '12px',
                fontWeight: '600',
                fontSize: '1.1rem',
                border: '2px solid hsl(220 13% 91%)',
                transition: 'all 0.2s',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
              onMouseOver={(e) => {
                e.target.style.background = 'hsl(220 13% 91%)';
                e.target.style.color = 'hsl(222.2 84% 4.9%)';
                e.target.style.transform = 'translateY(-2px)';
              }}
              onMouseOut={(e) => {
                e.target.style.background = 'hsl(0 0% 100%)';
                e.target.style.color = 'hsl(222.2 84% 4.9%)';
                e.target.style.transform = 'translateY(0)';
              }}
            >
              Back to Home
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default About; 