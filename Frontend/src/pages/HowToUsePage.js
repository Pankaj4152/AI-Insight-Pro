import React, { useState } from 'react';
import { User, Shield, CheckCircle, AlertTriangle, FileText, Database, Search, BarChart3, Download, HelpCircle } from 'lucide-react';

const HowToUsePage = () => {
  const [activeTab, setActiveTab] = useState('admin');

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
            Steps To Use The Product
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
            Complete guide to navigate and utilize AI-Insight-Pro effectively
          </p>
        </div>

        {/* Tab Navigation */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          marginBottom: '3rem'
        }}>
          <div style={{
            display: 'flex',
            background: 'rgba(255, 255, 255, 0.95)',
            borderRadius: '15px',
            padding: '0.5rem',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.2)'
          }}>
            <button
              onClick={() => setActiveTab('admin')}
              style={{
                padding: '1rem 2rem',
                borderRadius: '12px',
                border: 'none',
                background: activeTab === 'admin'
                  ? 'linear-gradient(135deg, hsl(198, 88%, 32%), hsl(172, 76%, 47%))'
                  : 'transparent',
                color: activeTab === 'admin' ? 'white' : 'hsl(215.4 16.3% 46.9%)',
                fontSize: '1.1rem',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                marginRight: '0.5rem'
              }}
            >
              <User style={{ width: '20px', height: '20px' }} />
              Admin Role
            </button>
            <button
              onClick={() => setActiveTab('compliance')}
              style={{
                padding: '1rem 2rem',
                borderRadius: '12px',
                border: 'none',
                background: activeTab === 'compliance'
                  ? 'linear-gradient(135deg, hsl(172, 76%, 47%), hsl(142, 76%, 36%))'
                  : 'transparent',
                color: activeTab === 'compliance' ? 'white' : 'hsl(215.4 16.3% 46.9%)',
                fontSize: '1.1rem',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}
            >
              <Shield style={{ width: '20px', height: '20px' }} />
              Compliance Officer
            </button>
          </div>
        </div>
        {/* Tab Content */}
        {activeTab === 'admin' && (
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
            padding: '3rem',
            borderRadius: '20px',
            marginBottom: '3rem',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: '2rem'
            }}>
              <User style={{
                width: '48px',
                height: '48px',
                color: 'hsl(198, 88%, 32%)',
                marginRight: '1rem'
              }} />
              <h2 style={{
                fontSize: '2.5rem',
                background: 'linear-gradient(135deg, hsl(198, 88%, 32%), hsl(172, 76%, 47%))',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                margin: 0,
                fontWeight: '700'
              }}>
                For Admin Role
              </h2>
            </div>

            <p style={{
              fontSize: '1.25rem',
              color: 'hsl(215.4 16.3% 46.9%)',
              marginBottom: '2rem',
              lineHeight: '1.6'
            }}>
              This role is defined for the company to store the risk analysis, set up SDEs and initial infrastructure.
            </p>
            {/* Admin Steps */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
              {/* Step 1 */}
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '1rem',
                padding: '1.5rem',
                background: 'rgba(198, 88, 32, 0.05)',
                borderRadius: '12px',
                border: '1px solid rgba(198, 88, 32, 0.1)'
              }}>
                <div style={{
                  background: 'hsl(198, 88%, 32%)',
                  color: 'white',
                  borderRadius: '50%',
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  flexShrink: 0
                }}>1</div>
                <div>
                  <h3 style={{ margin: '0 0 0.5rem 0', color: 'hsl(215.4 16.3% 15%)' }}>Sign Up Process</h3>
                  <p style={{ margin: 0, color: 'hsl(215.4 16.3% 46.9%)', lineHeight: '1.6' }}>
                    Click on "Get Started" button, choose Admin profile, and fill the sign-up form. Ensure the credentials are correct.
                  </p>
                </div>
              </div>
              {/* Step 2 */}
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '1rem',
                padding: '1.5rem',
                background: 'rgba(198, 88, 32, 0.05)',
                borderRadius: '12px',
                border: '1px solid rgba(198, 88, 32, 0.1)'
              }}>
                <div style={{
                  background: 'hsl(198, 88%, 32%)',
                  color: 'white',
                  borderRadius: '50%',
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  flexShrink: 0
                }}>2</div>
                <div>
                  <h3 style={{ margin: '0 0 0.5rem 0', color: 'hsl(215.4 16.3% 15%)' }}>Add SDEs (Sensitive Data Elements)</h3>
                  <p style={{ margin: '0 0 1rem 0', color: 'hsl(215.4 16.3% 46.9%)', lineHeight: '1.6' }}>
                    Add SDEs related to industries which help in analyzing risk in data. Add SDEs of your industry and additionally select SDEs from all-industries domain that ensure general SDEs. Admin needs to save the changes before moving further.
                  </p>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '1rem',
                    background: 'rgba(255, 193, 7, 0.1)',
                    borderRadius: '8px',
                    border: '1px solid rgba(255, 193, 7, 0.3)'
                  }}>
                    <AlertTriangle style={{ width: '20px', height: '20px', color: 'hsl(48, 96%, 53%)' }} />
                    <span style={{ color: 'hsl(48, 96%, 35%)', fontWeight: '500' }}>
                      <strong>Caution:</strong> Admins are free to remove SDEs in initial state. Any future deletion might not be an option for certain used SDEs.
                    </span>
                  </div>
                </div>
              </div>
              {/* Step 3 */}
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '1rem',
                padding: '1.5rem',
                background: 'rgba(198, 88, 32, 0.05)',
                borderRadius: '12px',
                border: '1px solid rgba(198, 88, 32, 0.1)'
              }}>
                <div style={{
                  background: 'hsl(198, 88%, 32%)',
                  color: 'white',
                  borderRadius: '50%',
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  flexShrink: 0
                }}>3</div>
                <div>
                  <h3 style={{ margin: '0 0 0.5rem 0', color: 'hsl(215.4 16.3% 15%)' }}>Set Up Model Registry (Optional)</h3>
                  <p style={{ margin: '0 0 1rem 0', color: 'hsl(215.4 16.3% 46.9%)', lineHeight: '1.6' }}>
                    Admin needs to set up Model Registry. It is optional and provides the feature of custom model for analysis.
                  </p>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '1rem',
                    background: 'rgba(33, 150, 243, 0.1)',
                    borderRadius: '8px',
                    border: '1px solid rgba(33, 150, 243, 0.3)'
                  }}>
                    <HelpCircle style={{ width: '20px', height: '20px', color: 'hsl(198, 88%, 32%)' }} />
                    <span style={{ color: 'hsl(198, 88%, 32%)', fontWeight: '500' }}>
                      <strong>Note:</strong> This feature is just reference here. Currently the product works on defined models.
                    </span>
                  </div>
                </div>
              </div>
              {/* Step 4 */}
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '1rem',
                padding: '1.5rem',
                background: 'rgba(198, 88, 32, 0.05)',
                borderRadius: '12px',
                border: '1px solid rgba(198, 88, 32, 0.1)'
              }}>
                <div style={{
                  background: 'hsl(198, 88%, 32%)',
                  color: 'white',
                  borderRadius: '50%',
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  flexShrink: 0
                }}>4</div>
                <div>
                  <h3 style={{ margin: '0 0 0.5rem 0', color: 'hsl(215.4 16.3% 15%)' }}>
                    <Database style={{ width: '20px', height: '20px', display: 'inline', marginRight: '0.5rem' }} />
                    Connect Page
                  </h3>
                  <p style={{ margin: 0, color: 'hsl(215.4 16.3% 46.9%)', lineHeight: '1.6' }}>
                    This page helps the admin add data sources. Choose from dropdown the different available options: GCP, BigQuery, PostgreSQL. After selecting option, enter the correct credentials. Import the credential file (Note: The file is not saved by us and is used as reference to ensure credibility). Once the connection is successful, click on Discover Page.
                  </p>
                </div>
              </div>
              {/* Step 5 */}
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '1rem',
                padding: '1.5rem',
                background: 'rgba(198, 88, 32, 0.05)',
                borderRadius: '12px',
                border: '1px solid rgba(198, 88, 32, 0.1)'
              }}>
                <div style={{
                  background: 'hsl(198, 88%, 32%)',
                  color: 'white',
                  borderRadius: '50%',
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  flexShrink: 0
                }}>5</div>
                <div>
                  <h3 style={{ margin: '0 0 0.5rem 0', color: 'hsl(215.4 16.3% 15%)' }}>
                    <Search style={{ width: '20px', height: '20px', display: 'inline', marginRight: '0.5rem' }} />
                    Discover Page
                  </h3>
                  <p style={{ margin: 0, color: 'hsl(215.4 16.3% 46.9%)', lineHeight: '1.6' }}>
                    The discover page helps admin see all the files stored in respective data source. Admin is allowed to scan all or partially scan the files by clicking on respective buttons. The scan process starts after submit that analyzes the selected files.
                  </p>
                </div>
              </div>
              {/* Step 6 */}
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '1rem',
                padding: '1.5rem',
                background: 'rgba(198, 88, 32, 0.05)',
                borderRadius: '12px',
                border: '1px solid rgba(198, 88, 32, 0.1)'
              }}>
                <div style={{
                  background: 'hsl(198, 88%, 32%)',
                  color: 'white',
                  borderRadius: '50%',
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  flexShrink: 0
                }}>6</div>
                <div>
                  <h3 style={{ margin: '0 0 0.5rem 0', color: 'hsl(215.4 16.3% 15%)' }}>View Scan Results</h3>
                  <p style={{ margin: 0, color: 'hsl(215.4 16.3% 46.9%)', lineHeight: '1.6' }}>
                    Once the scanning is performed, it would show the findings below. For details, you could click on Risk Assessment button or click on Dashboard on navbar.
                  </p>
                </div>
              </div>
              {/* Step 7 */}
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '1rem',
                padding: '1.5rem',
                background: 'rgba(198, 88, 32, 0.05)',
                borderRadius: '12px',
                border: '1px solid rgba(198, 88, 32, 0.1)'
              }}>
                <div style={{
                  background: 'hsl(198, 88%, 32%)',
                  color: 'white',
                  borderRadius: '50%',
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  flexShrink: 0
                }}>7</div>
                <div>
                  <h3 style={{ margin: '0 0 0.5rem 0', color: 'hsl(215.4 16.3% 15%)' }}>
                    <BarChart3 style={{ width: '20px', height: '20px', display: 'inline', marginRight: '0.5rem' }} />
                    Dashboard and Risk Analysis
                  </h3>
                  <p style={{ margin: 0, color: 'hsl(215.4 16.3% 46.9%)', lineHeight: '1.6' }}>
                    The Dashboard and Risk section helps viewing the risk analysis on the given data. Shows data sources connected, scan status, findings, risk score, confidence score, SDEs found in the findings. These pages provide visual and easy to understand preview to grasp knowledge about data.
                  </p>
                </div>
              </div>
              {/* Step 8 */}
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '1rem',
                padding: '1.5rem',
                background: 'rgba(198, 88, 32, 0.05)',
                borderRadius: '12px',
                border: '1px solid rgba(198, 88, 32, 0.1)'
              }}>
                <div style={{
                  background: 'hsl(198, 88%, 32%)',
                  color: 'white',
                  borderRadius: '50%',
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  flexShrink: 0
                }}>8</div>
                <div>
                  <h3 style={{ margin: '0 0 0.5rem 0', color: 'hsl(215.4 16.3% 15%)' }}>
                    <CheckCircle style={{ width: '20px', height: '20px', display: 'inline', marginRight: '0.5rem' }} />
                    Compliance Page
                  </h3>
                  <p style={{ margin: 0, color: 'hsl(215.4 16.3% 46.9%)', lineHeight: '1.6' }}>
                    Admin can select Compliance page and click on generate button to view the compliance report that matches the SDEs selected and findings to ensure how much compliant the data is and with which field.
                  </p>
                </div>
              </div>
              {/* Step 9 */}
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '1rem',
                padding: '1.5rem',
                background: 'rgba(198, 88, 32, 0.05)',
                borderRadius: '12px',
                border: '1px solid rgba(198, 88, 32, 0.1)'
              }}>
                <div style={{
                  background: 'hsl(198, 88%, 32%)',
                  color: 'white',
                  borderRadius: '50%',
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  flexShrink: 0
                }}>9</div>
                <div>
                  <h3 style={{ margin: '0 0 0.5rem 0', color: 'hsl(215.4 16.3% 15%)' }}>
                    <Download style={{ width: '20px', height: '20px', display: 'inline', marginRight: '0.5rem' }} />
                    Report and ASK Page
                  </h3>
                  <p style={{ margin: 0, color: 'hsl(215.4 16.3% 46.9%)', lineHeight: '1.6' }}>
                    The Report page provides downloadable report option on the risk analysis. Additionally, the ASK page helps to enquire about data that was fed into the system.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
        {activeTab === 'compliance' && (
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
            padding: '3rem',
            borderRadius: '20px',
            marginBottom: '3rem',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: '2rem'
            }}>
              <Shield style={{
                width: '48px',
                height: '48px',
                color: 'hsl(172, 76%, 47%)',
                marginRight: '1rem'
              }} />
              <h2 style={{
                fontSize: '2.5rem',
                background: 'linear-gradient(135deg, hsl(172, 76%, 47%), hsl(142, 76%, 36%))',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                margin: 0,
                fontWeight: '700'
              }}>
                For Compliance Officer Role
              </h2>
            </div>
            <p style={{
              fontSize: '1.25rem',
              color: 'hsl(215.4 16.3% 46.9%)',
              marginBottom: '2rem',
              lineHeight: '1.6'
            }}>
              For higher authority to view the data analytics and observe the pattern. They can use the compliance officer role.
            </p>
            {/* Compliance Officer Steps */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
              {/* Step 1 */}
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '1rem',
                padding: '1.5rem',
                background: 'rgba(172, 76, 47, 0.05)',
                borderRadius: '12px',
                border: '1px solid rgba(172, 76, 47, 0.1)'
              }}>
                <div style={{
                  background: 'hsl(172, 76%, 47%)',
                  color: 'white',
                  borderRadius: '50%',
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  flexShrink: 0
                }}>1</div>
                <div>
                  <h3 style={{ margin: '0 0 0.5rem 0', color: 'hsl(215.4 16.3% 15%)' }}>Sign Up as Compliance Officer</h3>
                  <p style={{ margin: 0, color: 'hsl(215.4 16.3% 46.9%)', lineHeight: '1.6' }}>
                    On "Get Started" button, select Compliance Officer role button that will redirect to sign-up page. It is understandable that compliance officer would have access to admin accounts, so before signing up here ensure to have at least one admin account for the company.
                  </p>
                </div>
              </div>
              {/* Step 2 */}
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '1rem',
                padding: '1.5rem',
                background: 'rgba(172, 76, 47, 0.05)',
                borderRadius: '12px',
                border: '1px solid rgba(172, 76, 47, 0.1)'
              }}>
                <div style={{
                  background: 'hsl(172, 76%, 47%)',
                  color: 'white',
                  borderRadius: '50%',
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  flexShrink: 0
                }}>2</div>
                <div>
                  <h3 style={{ margin: '0 0 0.5rem 0', color: 'hsl(215.4 16.3% 15%)' }}>Complete Registration Process</h3>
                  <p style={{ margin: 0, color: 'hsl(215.4 16.3% 46.9%)', lineHeight: '1.6' }}>
                    The sign-up page initially asks about the username, email and password for the officer. Later, they need to enter the company name. This helps in ensuring that the officer is someone trustable from the company. Once the company is verified, they need to add admin username and email they want to view reports of. Click on verify button that ensures the admin's credentials exist in the database. Currently, the officer can add 3 accounts detail.
                  </p>
                </div>
              </div>
              {/* Step 3 */}
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '1rem',
                padding: '1.5rem',
                background: 'rgba(172, 76, 47, 0.05)',
                borderRadius: '12px',
                border: '1px solid rgba(172, 76, 47, 0.1)'
              }}>
                <div style={{
                  background: 'hsl(172, 76%, 47%)',
                  color: 'white',
                  borderRadius: '50%',
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  flexShrink: 0
                }}>3</div>
                <div>
                  <h3 style={{ margin: '0 0 0.5rem 0', color: 'hsl(215.4 16.3% 15%)' }}>Login and Access Dashboard</h3>
                  <p style={{ margin: 0, color: 'hsl(215.4 16.3% 46.9%)', lineHeight: '1.6' }}>
                    After sign-up, they need to login and then will be redirected to the product. For the officer, they can see Dashboard, Risk Assessment, Report and Compliance similarly as mentioned in admin role. To view report of another admin, the officer needs to choose the account from dropdown. In this way they can view the report of any admin they want.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
        {/* Call to Action */}
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
              background: 'linear-gradient(135deg, hsl(198, 88%, 32%) 0%, hsl(172, 76%, 47%) 100%)',
              borderRadius: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginRight: '1rem'
            }}>
              <User size={30} color="white" />
            </div>
            <h2 style={{
              fontSize: '2.25rem',
              fontWeight: '700',
              color: 'hsl(215.4 16.3% 15%)',
              margin: 0
            }}>Ready to Get Started?</h2>
          </div>
          <p style={{
            fontSize: '1.125rem',
            color: 'hsl(215.4 16.3% 46.9%)',
            lineHeight: '1.8',
            marginBottom: '2rem',
            maxWidth: '600px',
            margin: '0 auto 2rem auto'
          }}>
            Choose your role and begin your journey with AI-Insight-Pro. Whether you're an admin setting up your organization's data protection or a compliance officer monitoring security standards, we've got you covered.
          </p>
          <div style={{
            display: 'flex',
            gap: '1rem',
            justifyContent: 'center',
            flexWrap: 'wrap'
          }}>
            <button
              onClick={() => window.location.href = '/signup'}
              style={{
                background: 'linear-gradient(135deg, hsl(198, 88%, 32%) 0%, hsl(172, 76%, 47%) 100%)',
                color: 'white',
                border: 'none',
                borderRadius: '12px',
                padding: '1rem 2rem',
                fontSize: '1.1rem',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                minWidth: '180px',
                justifyContent: 'center',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.background = 'linear-gradient(135deg, hsl(198, 98%, 22%) 0%, hsl(172, 86%, 37%) 100%)';
                e.target.style.boxShadow = '0 10px 15px -3px rgba(0, 0, 0, 0.2)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.background = 'linear-gradient(135deg, hsl(198, 88%, 32%) 0%, hsl(172, 76%, 47%) 100%)';
                e.target.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
              }}
            >
              <User style={{ width: '20px', height: '20px' }} />
              Start as Admin
            </button>
            <button
              onClick={() => window.location.href = '/role-signup'}
              style={{
                background: 'transparent',
                color: 'hsl(172, 76%, 47%)',
                border: '2px solid hsl(172, 76%, 47%)',
                borderRadius: '12px',
                padding: '1rem 2rem',
                fontSize: '1.1rem',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                minWidth: '180px',
                justifyContent: 'center'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = 'linear-gradient(135deg, hsl(172, 76%, 47%) 0%, hsl(142, 76%, 36%) 100%)';
                e.target.style.color = 'white';
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.borderColor = 'transparent';
                e.target.style.boxShadow = '0 10px 15px -3px rgba(0, 0, 0, 0.2)';
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'transparent';
                e.target.style.color = 'hsl(172, 76%, 47%)';
                e.target.style.transform = 'translateY(0)';
                e.target.style.borderColor = 'hsl(172, 76%, 47%)';
                e.target.style.boxShadow = 'none';
              }}
            >
              <Shield style={{ width: '20px', height: '20px' }} />
              Join as Compliance Officer
            </button>
            <button
              onClick={() => window.location.href = '/about'}
              style={{
                background: 'hsl(0 0% 100%)',
                color: 'hsl(215.4 16.3% 15%)',
                border: '2px solid hsl(220 13% 91%)',
                borderRadius: '12px',
                padding: '1rem 2rem',
                fontSize: '1.1rem',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                minWidth: '180px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = 'hsl(220 13% 91%)';
                e.target.style.color = 'hsl(215.4 16.3% 15%)';
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 10px 15px -3px rgba(0, 0, 0, 0.1)';
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'hsl(0 0% 100%)';
                e.target.style.color = 'hsl(215.4 16.3% 15%)';
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
              }}
            >
              Learn More
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
export default HowToUsePage;