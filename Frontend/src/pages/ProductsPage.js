import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Shield, Search, Lock, FileCheck, Bell, Sparkles } from 'lucide-react';

const productsData = [
  {
    id: 'data-discovery',
    title: 'AI-Powered Data Discovery & Classification',
    description: 'Automatically scan, detect, and classify personal, sensitive, and regulated data across all your enterprise data sources, on-premises and in the cloud.',
    route: '/products/data-discovery',
    icon: <Search size={32} />,
    gradient: 'linear-gradient(135deg, hsl(262 83% 58%) 0%, hsl(262 83% 48%) 100%)'
  },
  {
    id: 'risk-scoring',
    title: 'PII Risk Scoring Engine',
    description: 'Assign intelligent, dynamic risk scores to identified PII and sensitive data based on its type, location, exposure, and business context, enabling prioritized remediation.',
    route: '/products/risk-scoring',
    icon: <Shield size={32} />,
    gradient: 'linear-gradient(135deg, hsl(142 76% 36%) 0%, hsl(142 86% 28%) 100%)'
  },
  {
    id: 'data-protection',
    title: 'Smart Data Protection',
    description: 'Implement automated data protection measures, including encryption, anonymization, and access controls, tailored to the sensitivity and risk level of your data assets.',
    route: '/products/data-protection',
    icon: <Lock size={32} />,
    gradient: 'linear-gradient(135deg, hsl(198 88% 32%) 0%, hsl(198 98% 22%) 100%)'
  },
  {
    id: 'compliance-automation',
    title: 'Compliance Automation',
    description: 'Streamline compliance with global regulations like GDPR, HIPAA, PCI-DSS, and India\'s DPDP Act through automated mapping, reporting, and workflow management.',
    route: '/products/compliance-automation',
    icon: <FileCheck size={32} />,
    gradient: 'linear-gradient(135deg, hsl(172 76% 47%) 0%, hsl(172 86% 37%) 100%)'
  },
  {
    id: 'alerts-audit',
    title: 'Real-Time Alerts & Audit Logs',
    description: 'Receive instant notifications for policy violations, anomalous data access patterns, and compliance breaches, with comprehensive audit trails for forensic analysis.',
    route: '/products/alerts-audit',
    icon: <Bell size={32} />,
    gradient: 'linear-gradient(135deg, hsl(43 96% 56%) 0%, hsl(25 95% 53%) 100%)'
  }
];

function ProductsPage() {
  const navigate = useNavigate();
  const [isVisible, setIsVisible] = useState({});

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
      { threshold: 0.1 } // Trigger when 10% of the element is visible
    );

    // Observe each product card for animation
    productsData.forEach(product => {
      const card = document.getElementById(`product-card-${product.id}`);
      if (card) {
        observer.observe(card);
      }
    });

    return () => {
      productsData.forEach(product => {
        const card = document.getElementById(`product-card-${product.id}`);
        if (card) {
          observer.unobserve(card);
        }
      });
      observer.disconnect();
    };
  }, []);

  const handleVisitClick = (route) => {
    navigate(route);
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, hsl(210 40% 96%) 0%, hsl(0 0% 98%) 100%)',
      color: 'hsl(222.2 84% 4.9%)'
    }}>
      {/* Hero Section */}
      <section style={{
        padding: '4rem 2rem',
        textAlign: 'center',
        background: 'linear-gradient(135deg, hsl(198 88% 32%) 0%, hsl(172 76% 47%) 50%, hsl(142 76% 36%) 100%)',
        color: 'hsl(0 0% 98%)',
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
            background: 'rgba(255, 255, 255, 0.1)',
            color: 'white',
            padding: '0.75rem 1.5rem',
            borderRadius: '50px',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            marginBottom: '2rem',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.2)'
          }}>
            <Sparkles size={20} />
            <span style={{ fontWeight: '600' }}>Enterprise Solutions</span>
          </div>
          
          <h1 style={{
            fontSize: '3.5rem',
            fontWeight: '800',
            marginBottom: '1.5rem',
            textShadow: '0 4px 8px rgba(0, 0, 0, 0.2)',
            lineHeight: '1.1'
          }}>
            Our{' '}
            <span style={{
              background: 'linear-gradient(135deg, hsl(43 96% 56%) 0%, hsl(25 95% 53%) 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              Products
            </span>
          </h1>
          
          <p style={{
            fontSize: '1.3rem',
            opacity: '0.95',
            maxWidth: '700px',
            margin: '0 auto',
            lineHeight: '1.6'
          }}>
            Explore AIInsightPro's suite of AI-powered solutions designed to secure your enterprise data and ensure compliance.
          </p>
        </div>
        
        {/* Background Effects */}
        <div style={{
          position: 'absolute',
          top: '10%',
          right: '-5%',
          width: '30%',
          height: '80%',
          background: 'radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%)',
          borderRadius: '50%',
          zIndex: 1
        }} />
      </section>

      {/* Product Cards Grid */}
      <section style={{
        padding: '4rem 2rem',
        maxWidth: '1400px',
        margin: '0 auto'
      }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))',
          gap: '2rem'
        }}>
          {productsData.map((product, index) => (
            <div
              key={product.id}
              id={`product-card-${product.id}`}
              style={{
                background: 'hsl(0 0% 100%)',
                borderRadius: '1.5rem',
                padding: '2.5rem',
                boxShadow: '0 20px 25px -5px hsl(0 0% 0% / 0.1), 0 10px 10px -5px hsl(0 0% 0% / 0.04)',
                border: '1px solid hsl(220 13% 91%)',
                transition: 'all 0.3s ease',
                position: 'relative',
                overflow: 'hidden',
                opacity: isVisible[`product-card-${product.id}`] ? 1 : 0,
                transform: isVisible[`product-card-${product.id}`] ? 'translateY(0)' : 'translateY(20px)',
                animationDelay: `${index * 0.1}s`
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-8px)';
                e.target.style.boxShadow = '0 25px 50px -12px hsl(0 0% 0% / 0.25)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 20px 25px -5px hsl(0 0% 0% / 0.1), 0 10px 10px -5px hsl(0 0% 0% / 0.04)';
              }}
            >
              {/* Gradient Background */}
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: '6px',
                background: product.gradient
              }} />
              
              {/* Icon */}
              <div style={{
                width: '80px',
                height: '80px',
                borderRadius: '1rem',
                background: product.gradient,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                marginBottom: '1.5rem'
              }}>
                {product.icon}
              </div>
              
              <h3 style={{
                fontSize: '1.5rem',
                fontWeight: '700',
                marginBottom: '1rem',
                color: 'hsl(222.2 84% 4.9%)',
                lineHeight: '1.3'
              }}>
                {product.title}
              </h3>
              
              <p style={{
                color: 'hsl(215.4 16.3% 46.9%)',
                lineHeight: '1.6',
                marginBottom: '2rem',
                fontSize: '1rem'
              }}>
                {product.description}
              </p>
              
              <button
                onClick={() => handleVisitClick(product.route)}
                style={{
                  background: product.gradient,
                  color: 'white',
                  border: 'none',
                  borderRadius: '0.75rem',
                  padding: '0.875rem 1.5rem',
                  fontSize: '1rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  width: 'fit-content'
                }}
                onMouseEnter={(e) => {
                  e.target.style.transform = 'translateX(4px)';
                  e.target.style.boxShadow = '0 10px 20px rgba(0, 0, 0, 0.2)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.transform = 'translateX(0)';
                  e.target.style.boxShadow = 'none';
                }}
              >
                Visit Product <ArrowRight size={18} />
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default ProductsPage;
