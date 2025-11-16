import React, { useState, useEffect } from 'react';
import { ShieldCheck, Bell, Settings, DatabaseIcon, BookmarkIcon, Quote, Globe, TrendingUp, CheckCircle2, SearchCheck, Rocket } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const LearnMorePage = () => {
  const [isVisible, setIsVisible] = useState({});
  const navigate = useNavigate();

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          setIsVisible(prev => ({
            ...prev,
            [entry.target.id]: entry.isIntersecting
          }));
        });
      },
      { threshold: 0.1 }
    );
    const sections = document.querySelectorAll('.section');
    sections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, []);

  const highlights = [
    { icon: <SearchCheck className="highlight-icon" />, title: "AI-Powered Data Discovery", description: "..." },
    { icon: <TrendingUp className="highlight-icon" />, title: "Dynamic Risk Scoring", description: "..." },
    { icon: <Settings className="highlight-icon" />, title: "Compliance Automation", description: "..." },
    { icon: <Bell className="highlight-icon" />, title: "Audit & Alerts Framework", description: "..." }
  ];

  const industries = [
    "Healthcare & Life Sciences", "Financial Services & FinTech", "E-Commerce & Retail",
    "Information Technology", "Public Sector & Government", "Legal & Compliance Firms"
  ];

  const roadmapItems = [
    { quarter: "Q4 2025", feature: "Automated DSAR Workflow Module", description: "Release automated Data Subject Access Request workflows" },
    { quarter: "Q1 2026", feature: "Real-time Privacy Risk APIs", description: "Launch compliance-as-a-service features and risk scoring APIs" },
    { quarter: "Mid-2026", feature: "Enterprise Integrations", description: "Native integrations for Snowflake, Databricks, and SAP Hana" },
    { quarter: "End 2026", feature: "AI Data Masking Engine", description: "Enhanced anonymization and tokenization with AI-based masking" }
  ];

  return (
    <div style={{
      minHeight: '100vh',
      background: 'hsl(0 0% 100%)'
    }}>
      {/* Hero Section */}
      <section style={{
        padding: '4rem 1rem',
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          position: 'relative',
          zIndex: 2
        }}>
          <div style={{
            background: 'hsl(0 0% 100%)',
            color: 'hsl(222.2 84% 4.9%)',
            padding: '0.75rem 1.5rem',
            borderRadius: '50px',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            marginBottom: '2rem',
            border: '1px solid hsl(220 13% 91%)',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}>
            <ShieldCheck size={20} />
            <span style={{ fontWeight: '600' }}>Enterprise Data Security</span>
          </div>
          
          <h1 className="page-title">
            AIInsightPro{' '}
            <span style={{
              color: 'hsl(198, 88%, 32%)',
              fontWeight: '800'
            }}>
              Data Guardian
            </span>
          </h1>
          
          <p style={{
            fontSize: '1.5rem',
            color: 'hsl(215.4 16.3% 46.9%)',
            margin: '0 0 3rem 0',
            maxWidth: '800px',
            marginLeft: 'auto',
            marginRight: 'auto',
            lineHeight: '1.6'
          }}>
            Advanced AI-powered data security and risk intelligence platform for modern enterprises
          </p>
          
          <div style={{
            display: 'flex',
            gap: '1rem',
            justifyContent: 'center',
            flexWrap: 'wrap',
            marginBottom: '4rem'
          }}>
            <button 
              onClick={() => navigate('/signup')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '1rem 2rem',
                background: 'linear-gradient(135deg, hsl(198 88% 32%), hsl(172 76% 47%))',
                color: 'white',
                border: 'none',
                borderRadius: '12px',
                fontWeight: '600',
                fontSize: '1.1rem',
                cursor: 'pointer',
                transition: 'all 0.2s',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
              onMouseOver={(e) => e.target.style.transform = 'translateY(-2px)'}
              onMouseOut={(e) => e.target.style.transform = 'translateY(0)'}
            >
              Get Started <Rocket size={20} />
            </button>
            
            <button style={{
              padding: '1rem 2rem',
              background: 'hsl(0 0% 100%)',
              color: 'hsl(222.2 84% 4.9%)',
              border: '2px solid hsl(220 13% 91%)',
              borderRadius: '12px',
              fontWeight: '600',
              fontSize: '1.1rem',
              cursor: 'pointer',
              transition: 'all 0.2s',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }}
            onMouseOver={(e) => {
              e.target.style.background = 'hsl(220 13% 91%)';
              e.target.style.transform = 'translateY(-2px)';
            }}
            onMouseOut={(e) => {
              e.target.style.background = 'hsl(0 0% 100%)';
              e.target.style.transform = 'translateY(0)';
            }}>
              Watch Demo
            </button>
          </div>
          
          {/* Floating Cards */}
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '2rem',
            flexWrap: 'wrap'
          }}>
            {[
              { icon: DatabaseIcon, label: 'Data Protected' },
              { icon: ShieldCheck, label: 'Threats Detected' },
              { icon: BookmarkIcon, label: 'Compliance Ready' }
            ].map((item, index) => (
              <div key={index} style={{
                background: 'hsl(0 0% 100%)',
                padding: '1.5rem',
                borderRadius: '16px',
                border: '1px solid hsl(220 13% 91%)',
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                color: 'hsl(222.2 84% 4.9%)',
                minWidth: '200px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}>
                <item.icon size={24} />
                <span style={{ fontWeight: '600' }}>{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* About Section */}
      <section style={{
        padding: '4rem 1rem',
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(10px)'
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          textAlign: 'center'
        }}>
          <h2 style={{
            fontSize: '2.5rem',
            fontWeight: '700',
            color: '#1f2937',
            marginBottom: '1.5rem'
          }}>About AIInsightPro</h2>
          <p style={{
            fontSize: '1.25rem',
            color: '#6b7280',
            lineHeight: '1.8',
            maxWidth: '800px',
            margin: '0 auto'
          }}>
            AIInsightPro empowers businesses to detect hidden personal and sensitive data, evaluate associated risks, 
            and proactively mitigate compliance and security gaps — all through an intuitive, scalable, 
            and cloud-ready platform.
          </p>
        </div>
      </section>

      {/* Key Features Grid */}
      <section style={{
        padding: '4rem 1rem',
        background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)'
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto'
        }}>
          <h2 style={{
            fontSize: '2.5rem',
            fontWeight: '700',
            color: '#1f2937',
            textAlign: 'center',
            marginBottom: '3rem'
          }}>Key Features</h2>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '2rem'
          }}>
            {[
              { 
                icon: SearchCheck, 
                title: "AI-Powered Data Discovery", 
                description: "Automatically detect and classify sensitive data across your entire infrastructure using advanced machine learning algorithms." 
              },
              { 
                icon: TrendingUp, 
                title: "Dynamic Risk Scoring", 
                description: "Real-time risk assessment and scoring based on data sensitivity, access patterns, and compliance requirements." 
              },
              { 
                icon: Settings, 
                title: "Compliance Automation", 
                description: "Streamline GDPR, CCPA, and other regulatory compliance with automated workflows and reporting." 
              },
              { 
                icon: Bell, 
                title: "Audit & Alerts Framework", 
                description: "Comprehensive monitoring with instant alerts for potential data breaches and compliance violations." 
              }
            ].map((feature, index) => (
              <div key={index} style={{
                background: 'white',
                padding: '2.5rem',
                borderRadius: '20px',
                textAlign: 'center',
                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
                transition: 'all 0.3s'
              }}
              onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-8px)'}
              onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}>
                <div style={{
                  width: '80px',
                  height: '80px',
                  background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                  borderRadius: '20px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 1.5rem',
                  color: 'white'
                }}>
                  <feature.icon size={36} />
                </div>
                <h3 style={{
                  fontSize: '1.5rem',
                  fontWeight: '700',
                  color: '#1f2937',
                  marginBottom: '1rem'
                }}>{feature.title}</h3>
                <p style={{
                  color: '#6b7280',
                  lineHeight: '1.6',
                  margin: 0
                }}>{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="vision-mission-section">
        <div className="container">
          <div className="vision-mission-grid">
            <div className="vision-card">
              <Globe className="vm-icon"/>
              <h3>Our Vision</h3>
              <p>
                To become the most trusted global platform for AI-powered data risk management and 
                compliance intelligence, enabling enterprises to secure sensitive information and 
                uphold customer privacy in a rapidly digitizing world.
              </p>
            </div>
            <div className="mission-card">
              <TrendingUp className="vm-icon" />
              <h3>Our Mission</h3>
              <p>
                To help organizations seamlessly discover, classify, and protect sensitive data assets 
                by delivering intelligent, automated, and actionable risk management solutions — 
                reducing exposure, ensuring regulatory compliance, and building digital trust.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section id="highlights" className={`section highlights-section ${isVisible.highlights ? 'visible' : ''}`}>
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">Platform Highlights</h2>
          </div>
          <div className="highlights-grid">
            {highlights.map((highlight, index) => (
              <div key={index} className="highlight-card" style={{ animationDelay: `${index * 0.1}s` }}>
                <div className="highlight-icon-wrapper">
                  {highlight.icon}
                </div>
                <h3 className="highlight-title">{highlight.title}</h3>
                <p className="highlight-description">{highlight.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="why-choose-section">
        <div className="container">
          <div className="why-choose-content">
            <div className="why-choose-text">
              <h2 className="section-title">Why Choose AIInsightPro</h2>
              <div className="features-list">
                <div className="feature-item">
                  <CheckCircle2 className="feature-icon" />
                  <span>Next-Gen AI Discovery Engine trained for complex environments</span>
                </div>
                <div className="feature-item">
                  <CheckCircle2 className="feature-icon" />
                  <span>Industry-Ready Compliance Packs for GDPR, HIPAA, PCI, and DPDP</span>
                </div>
                <div className="feature-item">
                  <CheckCircle2 className="feature-icon" />
                  <span>Enterprise-Grade Risk Heatmaps and Scoring Models</span>
                </div>
                <div className="feature-item">
                  <CheckCircle2 className="feature-icon" />
                  <span>API-First Architecture for seamless integrations</span>
                </div>
                <div className="feature-item">
                  <CheckCircle2 className="feature-icon" />
                  <span>Privacy by Design and Security by Default</span>
                </div>
              </div>
            </div>
            <div className="why-choose-visual">
              <div className="stats-card">
                <div className="stat-item">
                  <span className="stat-number">500GB+</span>
                  <span className="stat-label">Data Analyzed</span>
                </div>
                <div className="stat-item">
                  <span className="stat-number">72hrs</span>
                  <span className="stat-label">Detection Time</span>
                </div>
                <div className="stat-item">
                  <span className="stat-number">99.9%</span>
                  <span className="stat-label">Accuracy Rate</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="industries-section">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">Industries We Serve</h2>
          </div>
          <div className="industries-grid">
            {industries.map((industry, index) => (
              <div key={index} className="industry-card">
                <span>{industry}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="testimonials-section">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">Trusted By</h2>
          </div>
          <div className="testimonials-grid">
            <div className="testimonial-card">
              <span className="testimonial-icon"><Quote/></span>
              <p className="testimonial-text">
                "AIInsightPro helped us identify over 500GB of unprotected sensitive data in 72 hours."
              </p>
              <div className="testimonial-author">
                <span className="author-name">CISO</span>
                <span className="author-title">Leading FinTech</span>
              </div>
            </div>
            <div className="testimonial-card">
              <span className="testimonial-icon"><Quote /></span>
              <p className="testimonial-text">
                "The risk dashboard provides our compliance team with real-time risk exposure we never had before."
              </p>
              <div className="testimonial-author">
                <span className="author-name">Data Privacy Officer</span>
                <span className="author-title">Global Retailer</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="roadmap" className={`section roadmap-section ${isVisible.roadmap ? 'visible' : ''}`}>
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">Our Roadmap</h2>
          </div>
          <div className="roadmap-timeline">
            {roadmapItems.map((item, index) => (
              <div key={index} className="roadmap-item">
                <div className="roadmap-marker"></div>
                <div className="roadmap-content">
                  <span className="roadmap-quarter">{item.quarter}</span>
                  <h3 className="roadmap-feature">{item.feature}</h3>
                  <p className="roadmap-description">{item.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Call to Action Section */}
      <section style={{
        padding: '4rem 1rem',
        background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
        textAlign: 'center'
      }}>
        <div style={{
          maxWidth: '800px',
          margin: '0 auto'
        }}>
          <h2 style={{
            fontSize: '2.5rem',
            fontWeight: '700',
            color: 'white',
            marginBottom: '1.5rem'
          }}>Ready to Secure Your Data?</h2>
          <p style={{
            fontSize: '1.25rem',
            color: 'rgba(255, 255, 255, 0.9)',
            marginBottom: '2rem',
            lineHeight: '1.6'
          }}>
            Join leading enterprises in protecting sensitive information with AI-powered intelligence.
          </p>
          <div style={{
            display: 'flex',
            gap: '1rem',
            justifyContent: 'center',
            flexWrap: 'wrap'
          }}>
            <button 
              onClick={() => navigate('/signup')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '1rem 2rem',
                background: 'white',
                color: '#4f46e5',
                border: 'none',
                borderRadius: '12px',
                fontWeight: '600',
                fontSize: '1.1rem',
                cursor: 'pointer',
                transition: 'all 0.2s',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
              onMouseOver={(e) => e.target.style.transform = 'translateY(-2px)'}
              onMouseOut={(e) => e.target.style.transform = 'translateY(0)'}
            >
              Start Free Trial <Rocket size={20} />
            </button>
            <button style={{
              padding: '1rem 2rem',
              background: 'transparent',
              color: 'white',
              border: '2px solid rgba(255, 255, 255, 0.3)',
              borderRadius: '12px',
              fontWeight: '600',
              fontSize: '1.1rem',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => {
              e.target.style.background = 'rgba(255, 255, 255, 0.1)';
              e.target.style.transform = 'translateY(-2px)';
            }}
            onMouseOut={(e) => {
              e.target.style.background = 'transparent';
              e.target.style.transform = 'translateY(0)';
            }}>
              Contact Sales
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default LearnMorePage;
