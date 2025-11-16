import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Shield, Brain, Users, TrendingUp, Award, BarChart3, Database, Eye, FileCheck } from 'lucide-react';
import RoleSelectionModal from '../components/RoleSelectionModal';
import '../Css/Home.css';



function Home() {
  const navigate = useNavigate();
  const [showRoleSelection, setShowRoleSelection] = useState(false);
  const [visibleSections, setVisibleSections] = useState({});

  useEffect(() => {
    // Ensure page starts at the top when component mounts
    // Use a small delay to work with transition effects
    const timer = setTimeout(() => {
      window.scrollTo({
        top: 0,
        left: 0,
        behavior: 'instant'
      });
    }, 50);
    
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          setVisibleSections(prev => ({
            ...prev,
            [entry.target.id]: entry.isIntersecting
          }));
        });
      },
      { threshold: 0.1 }
    );

    const sections = document.querySelectorAll('.animate-section');
    sections.forEach((section) => observer.observe(section));

    return () => {
      clearTimeout(timer);
      observer.disconnect();
    };
  }, []);

  const handleGetStartedClick = () => {
    setShowRoleSelection(true);
  };

  const handleRoleSelection = (role) => {
    if (role === 'admin') {
      navigate('/signup');
    } else if (role === 'compliance_officer') {
      navigate('/role-signup');
    }
  };

  const handleAboutClick = () => {
    navigate('/about');
  };



  const handleDashboardClick = () => {
    navigate('/dashboard');
  };

  return (
    <div style={{ fontFamily: 'var(--font-family)' }}>
      {/* Hero Section */}
      <section id="home" className={`home-section animate-section ${visibleSections.home ? 'visible' : ''}`} style={{
        minHeight: '100vh',
        background: 'hsl(0 0% 100%)',
        color: 'hsl(142 76% 36%)',
        display: 'flex',
        alignItems: 'center',
        position: 'relative',
        overflow: 'hidden',
        padding: '1rem'
      }}>
        <div className="background-eclipse" />
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          padding: 'clamp(1rem, 4vw, 2rem)',
          position: 'relative',
          zIndex: 2,
          textAlign: 'center',
          width: '100%'
        }}>
          <h1 style={{
            fontSize: 'clamp(2rem, 8vw, 4rem)',
            fontWeight: '800',
            marginBottom: '1.5rem',
            letterSpacing: '-0.02em',
            lineHeight: '1.1'
          }}>
            <span style={{
              background: 'linear-gradient(135deg, hsl(198 88% 32%) 0%, hsl(172 76% 47%) 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              AI-Insight-Pro
            </span>
          </h1>
          
          <h2 style={{
            fontSize: 'clamp(1.2rem, 5vw, 1.8rem)',
            fontWeight: '600',
            marginBottom: '2rem',
            maxWidth: '800px',
            margin: '0 auto 2rem auto',
            lineHeight: '1.4',
            background: 'linear-gradient(135deg, hsl(198 88% 32%) 0%, hsl(172 76% 47%) 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}>
            Unleashing Brilliant Decisions with AI-Powered Clarity
          </h2>
          
          <p style={{
            fontSize: 'clamp(1rem, 3vw, 1.2rem)',
            marginBottom: '3rem',
            maxWidth: '600px',
            margin: '0 auto 3rem auto',
            lineHeight: '1.6',
            color: 'hsl(215.4 16.3% 46.9%)'
          }}>
            AI-Insight-Pro is an advanced AI-powered platform designed to identify, assess, and secure sensitive data across your enterprise.
          </p>

          <div style={{
            display: 'flex',
            gap: 'clamp(1rem, 3vw, 1.5rem)',
            justifyContent: 'center',
            flexWrap: 'wrap',
            marginBottom: '4rem'
          }}>
            <button
              onClick={handleGetStartedClick}
              style={{
                background: 'linear-gradient(135deg, hsl(198 88% 32%) 0%, hsl(172 76% 47%) 100%)',
                color: 'hsl(0 0% 100%)',
                border: 'none',
                borderRadius: '0.75rem',
                padding: 'clamp(0.75rem, 2vw, 1rem) clamp(1.5rem, 4vw, 2rem)',
                fontSize: 'clamp(1rem, 2.5vw, 1.1rem)',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                minWidth: 'clamp(150px, 30vw, 180px)',
                justifyContent: 'center'
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.background = 'linear-gradient(135deg, hsl(198 98% 22%) 0%, hsl(172 86% 37%) 100%)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.background = 'linear-gradient(135deg, hsl(198 88% 32%) 0%, hsl(172 76% 47%) 100%)';
              }}
            >
              Get Started <ArrowRight size={20} />
            </button>
            
            <button
              onClick={handleAboutClick}
              style={{
                background: 'transparent',
                color: 'hsl(198 88% 32%)',
                border: '2px solid hsl(198 88% 32%)',
                borderRadius: '0.75rem',
                padding: 'clamp(0.75rem, 2vw, 1rem) clamp(1.5rem, 4vw, 2rem)',
                fontSize: 'clamp(1rem, 2.5vw, 1.1rem)',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                minWidth: 'clamp(150px, 30vw, 180px)'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = 'linear-gradient(135deg, hsl(198 88% 32%) 0%, hsl(172 76% 47%) 100%)';
                e.target.style.color = 'hsl(0 0% 100%)';
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.borderColor = 'transparent';
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'transparent';
                e.target.style.color = 'hsl(198 88% 32%)';
                e.target.style.transform = 'translateY(0)';
                e.target.style.borderColor = 'hsl(198 88% 32%)';
              }}
            >
              About Us
            </button>
          </div>

          {/* Floating stats */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(clamp(180px, 40vw, 200px), 1fr))',
            gap: 'clamp(1rem, 4vw, 2rem)',
            maxWidth: '800px',
            margin: '0 auto'
          }}>
            {[
              { icon: <Users size={24} />, number: '500+', label: 'Enterprise Clients' },
              { icon: <Shield size={24} />, number: '99.9%', label: 'Data Protection' },
              { icon: <TrendingUp size={24} />, number: '24/7', label: 'Monitoring' },
              { icon: <Award size={24} />, number: 'ISO 27001', label: 'Certified' }
            ].map((stat, index) => (
              <div key={index} style={{
                background: 'hsl(0 0% 100%)',
                border: '1px solid hsl(220 13% 91%)',
                borderRadius: '1rem',
                padding: 'clamp(1rem, 3vw, 1.5rem)',
                textAlign: 'center'
              }}>
                <div style={{ marginBottom: '0.5rem', color: 'hsl(198 88% 32%)' }}>
                  {stat.icon}
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: '700', marginBottom: '0.25rem' }}>
                  <span style={{
                    background: 'linear-gradient(135deg, hsl(198 88% 32%) 0%, hsl(172 76% 47%) 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text'
                  }}>
                    {stat.number}
                  </span>
                </div>
                <div style={{ fontSize: '0.9rem', color: 'hsl(215.4 16.3% 46.9%)' }}>
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="background-eclipse2" />
      </section>

      {/* Features Section */}
      <section id="features" className={`animate-section ${visibleSections.features ? 'visible' : ''}`} style={{
        padding: 'clamp(3rem, 8vw, 5rem) clamp(1rem, 4vw, 2rem)',
        background: 'hsl(0 0% 100%)',
        borderTop: '1px solid hsl(220 13% 91%)',
        opacity: visibleSections.features ? 1 : 0,
        transform: visibleSections.features ? 'translateY(0)' : 'translateY(50px)',
        transition: 'all 0.8s ease'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 'clamp(2rem, 6vw, 4rem)' }}>
            <h2 style={{
              fontSize: 'clamp(1.8rem, 6vw, 2.5rem)',
              fontWeight: '800',
              marginBottom: '1rem'
            }}>
              <span style={{
                background: 'linear-gradient(135deg, hsl(198 88% 32%) 0%, hsl(172 76% 47%) 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}>
                Powerful Features for
              </span>{' '}
              <span style={{
                background: 'linear-gradient(135deg, hsl(172 76% 47%) 0%, hsl(142 76% 36%) 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}>
                Enterprise Security
              </span>
            </h2>
            <p style={{
              fontSize: 'clamp(1rem, 3vw, 1.2rem)',
              color: 'hsl(215.4 16.3% 46.9%)',
              maxWidth: '600px',
              margin: '0 auto'
            }}>
              Comprehensive AI-powered solutions to protect your most valuable asset - your data
            </p>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(clamp(280px, 45vw, 350px), 1fr))',
            gap: 'clamp(1.5rem, 4vw, 2rem)'
          }}>
            {[
              {
                icon: <Database size={32} />,
                title: 'Data Discovery & Classification',
                description: 'Automatically scan and classify sensitive data across all your enterprise systems with AI-powered precision.',
                gradient: 'linear-gradient(135deg, hsl(262 83% 58%), hsl(262 83% 48%))'
              },
              {
                icon: <BarChart3 size={32} />,
                title: 'Risk Assessment Engine',
                description: 'Intelligent risk scoring and assessment to prioritize your security efforts where they matter most.',
                gradient: 'linear-gradient(135deg, hsl(142 76% 36%), hsl(142 86% 28%))'
              },
              {
                icon: <Shield size={32} />,
                title: 'Advanced Data Protection',
                description: 'Multi-layered security controls including encryption, access management, and data loss prevention.',
                gradient: 'linear-gradient(135deg, hsl(198 88% 32%), hsl(198 98% 22%))'
              },
              {
                icon: <Eye size={32} />,
                title: 'Real-time Monitoring',
                description: 'Continuous surveillance with instant alerts for anomalies, breaches, and compliance violations.',
                gradient: 'linear-gradient(135deg, hsl(172 76% 47%), hsl(172 86% 37%))'
              },
              {
                icon: <FileCheck size={32} />,
                title: 'Compliance Automation',
                description: 'Streamline compliance with GDPR, HIPAA, SOX, and other regulations through automated workflows.',
                gradient: 'linear-gradient(135deg, hsl(43 96% 56%), hsl(25 95% 53%))'
              },
              {
                icon: <Brain size={32} />,
                title: 'AI-Powered Insights',
                description: 'Machine learning algorithms provide predictive analytics and intelligent recommendations.',
                gradient: 'linear-gradient(135deg, hsl(310 75% 58%), hsl(310 85% 48%))'
              }
            ].map((feature, index) => (
              <div key={index} style={{
                background: 'hsl(0 0% 100%)',
                borderRadius: '1.5rem',
                padding: 'clamp(1.5rem, 4vw, 2.5rem)',
                boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)',
                border: '1px solid hsl(220 13% 91%)',
                transition: 'all 0.3s ease',
                position: 'relative',
                overflow: 'hidden'
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-5px)';
                e.target.style.boxShadow = '0 20px 40px -5px rgba(0, 0, 0, 0.15)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 10px 25px -5px rgba(0, 0, 0, 0.1)';
              }}>
                <div style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  height: '4px',
                  background: feature.gradient
                }} />
                
                <div style={{
                  width: '60px',
                  height: '60px',
                  borderRadius: '1rem',
                  background: feature.gradient,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  marginBottom: '1.5rem'
                }}>
                  {feature.icon}
                </div>
                
                <h3 style={{
                  fontSize: 'clamp(1.1rem, 3vw, 1.4rem)',
                  fontWeight: '700',
                  marginBottom: '1rem',
                  color: 'hsl(222.2 84% 4.9%)'
                }}>
                  {feature.title}
                </h3>
                
                <p style={{
                  color: 'hsl(215.4 16.3% 46.9%)',
                  lineHeight: '1.6'
                }}>
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section id="cta" className={`animate-section ${visibleSections.cta ? 'visible' : ''}`} style={{
        padding: 'clamp(2rem, 6vw, 4rem) clamp(1rem, 4vw, 2rem)',
        background: 'hsl(0 0% 100%)',
        borderTop: '1px solid hsl(220 13% 91%)',
        textAlign: 'center',
        transform: visibleSections.cta ? 'translateY(0)' : 'translateY(50px)',
        transition: 'all 0.8s ease'
      }}>
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
          <h2 style={{
            fontSize: 'clamp(1.8rem, 6vw, 2.5rem)',
            fontWeight: '700',
            marginBottom: '1.5rem'
          }}>
            <span style={{
              background: 'linear-gradient(135deg, hsl(198 88% 32%) 0%, hsl(172 76% 47%) 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              Ready to Secure Your Enterprise?
            </span>
          </h2>
          <p style={{
            fontSize: 'clamp(1rem, 3vw, 1.2rem)',
            marginBottom: '3rem',
            lineHeight: '1.6',
            color: 'hsl(215.4 16.3% 46.9%)'
          }}>
            Join thousands of organizations worldwide who trust AI-Insight-Pro to protect their most sensitive data. Start your free trial today.
          </p>
          <div style={{
            display: 'flex',
            gap: 'clamp(0.75rem, 2vw, 1rem)',
            justifyContent: 'center',
            flexWrap: 'wrap'
          }}>
            <button
              onClick={handleGetStartedClick}
              style={{
                background: 'linear-gradient(135deg, hsl(198 88% 32%) 0%, hsl(172 76% 47%) 100%)',
                color: 'white',
                border: 'none',
                borderRadius: '0.75rem',
                padding: 'clamp(0.75rem, 2vw, 1rem) clamp(1.5rem, 4vw, 2rem)',
                fontSize: 'clamp(1rem, 2.5vw, 1.1rem)',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.background = 'linear-gradient(135deg, hsl(198 98% 22%) 0%, hsl(172 86% 37%) 100%)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.background = 'linear-gradient(135deg, hsl(198 88% 32%) 0%, hsl(172 76% 47%) 100%)';
              }}
            >
              Start Free Trial <ArrowRight size={20} />
            </button>
            
            <button
              onClick={handleDashboardClick}
              style={{
                background: 'transparent',
                color: 'hsl(198 88% 32%)',
                border: '2px solid hsl(198 88% 32%)',
                borderRadius: '0.75rem',
                padding: 'clamp(0.75rem, 2vw, 1rem) clamp(1.5rem, 4vw, 2rem)',
                fontSize: 'clamp(1rem, 2.5vw, 1.1rem)',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s ease'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = 'linear-gradient(135deg, hsl(198 88% 32%) 0%, hsl(172 76% 47%) 100%)';
                e.target.style.color = 'white';
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.borderColor = 'transparent';
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'transparent';
                e.target.style.color = 'hsl(198 88% 32%)';
                e.target.style.transform = 'translateY(0)';
                e.target.style.borderColor = 'hsl(198 88% 32%)';
              }}
            >
              View Dashboard
            </button>
          </div>
        </div>
      </section>

      {/* Role Selection Modal */}
      <RoleSelectionModal
        isOpen={showRoleSelection}
        onClose={() => setShowRoleSelection(false)}
        onRoleSelect={handleRoleSelection}
      />
    </div>
  );
}

export default Home;