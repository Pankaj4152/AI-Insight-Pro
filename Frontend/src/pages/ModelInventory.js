import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL_CONNECTOR } from '../apiConfig';
import { getCurrentClientId } from '../utils/clientUtils';
import '../Css/App.css';

function ModelInventoryPage() {
  const navigate = useNavigate();
  const [models, setModels] = useState([]);
  const [form, setForm] = useState({
    model_name: '',
    model_name_dropdown: '',
    model_name_custom: '',
    provider_name: '',
    provider_name_dropdown: '',
    provider_name_custom: '',
    weights_location: '',
    bias_notes: '',
    description: '',
    industry_use_case: '',
    data_store_types: '',
    compliance_requirements: ''
  });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [showDetails, setShowDetails] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [modelToDelete, setModelToDelete] = useState(null);
  const [isSignupFlow, setIsSignupFlow] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [analytics, setAnalytics] = useState({
    totalModels: 0,
    industryBreakdown: {},
    dataStoreBreakdown: {},
    complianceBreakdown: {}
  });
  const [activeTab, setActiveTab] = useState('view'); // 'view' or 'add'
  
  // Get client_id with fallback for signup flow
  const getClientId = () => {
    let client_id = getCurrentClientId();
    if (!client_id && isSignupFlow) {
      // During signup flow, try to get from user object as fallback
      const userObj = localStorage.getItem('user');
      if (userObj) {
        try {
          const parsed = JSON.parse(userObj);
          client_id = parsed.client_id;
        } catch (e) {
          console.warn('Failed to parse user object');
        }
      }
    }
    return client_id;
  };

  const fetchModels = async () => {
    setError('');
    const client_id = getClientId();
    
    // During signup flow, it's OK to not have models yet
    if (!client_id && !isSignupFlow) {
      setError('No client ID available. Please log in again.');
      return;
    }
    
    // Skip fetching during signup if no client_id (it's optional)
    if (!client_id && isSignupFlow) {
      setModels([]);
      return;
    }
    
    try {
      const res = await fetch(`${API_BASE_URL_CONNECTOR}/model-inventory/list?client_id=${client_id || ''}`);
      if (!res.ok) {
        const data = await res.json();
        let errorMessage = 'Failed to load models.';
        if (data.detail) {
          if (typeof data.detail === 'string') {
            errorMessage = data.detail;
          } else if (Array.isArray(data.detail)) {
            errorMessage = data.detail.map(e => e.msg || e.message || e).join(' ');
          } else {
            errorMessage = JSON.stringify(data.detail);
          }
        }
        setError(errorMessage);
        setModels([]);
        return;
      }
      const data = await res.json();
      console.log('Raw API response:', data); // Debug log
      console.log('Models received:', data.models); // Debug log
      console.log('First model details:', data.models && data.models[0]); // Debug log to see all fields
      
      // Enhanced debug logging for each field
      if (data.models && data.models.length > 0) {
        data.models.forEach((model, index) => {
          console.log(`Model ${index + 1}:`, {
            name: model.model_name,
            industry: model.industry_use_case,
            dataStores: model.data_store_types,
            compliance: model.compliance_requirements,
            allFields: Object.keys(model)
          });
        });
      }
      
      setModels(Array.isArray(data.models) ? data.models : []);
      
      // Calculate analytics
      const modelList = Array.isArray(data.models) ? data.models : [];
      console.log('Models for analytics:', modelList); // Debug log
      calculateAnalytics(modelList);
    } catch (error) {
      setError('Error loading models.');
      setModels([]);
    }
  };

  const calculateAnalytics = (modelList) => {
    console.log('calculateAnalytics called with:', modelList); // Debug log
    console.log('Number of models:', modelList.length);
    const industryBreakdown = {};
    const dataStoreBreakdown = {};
    const complianceBreakdown = {};

    modelList.forEach((model, index) => {
      console.log(`Processing model ${index + 1}:`, {
        name: model.model_name,
        industry: model.industry_use_case,
        dataStores: model.data_store_types,
        compliance: model.compliance_requirements,
        industryType: typeof model.industry_use_case,
        dataStoresType: typeof model.data_store_types,
        complianceType: typeof model.compliance_requirements
      });
      
      // Industry breakdown
      const industry = model.industry_use_case || 'Not specified';
      industryBreakdown[industry] = (industryBreakdown[industry] || 0) + 1;
      console.log(`Industry "${industry}" count now:`, industryBreakdown[industry]);

      // Data store breakdown
      if (model.data_store_types && model.data_store_types !== null && model.data_store_types.trim() !== '') {
        console.log('Processing data stores:', model.data_store_types);
        const stores = model.data_store_types.split(',');
        console.log('Split stores:', stores);
        stores.forEach(store => {
          const trimmedStore = store.trim();
          if (trimmedStore) {
            // Convert to lowercase to make it case-insensitive
            const normalizedStore = trimmedStore.toLowerCase();
            dataStoreBreakdown[normalizedStore] = (dataStoreBreakdown[normalizedStore] || 0) + 1;
            console.log(`Data store "${normalizedStore}" count now:`, dataStoreBreakdown[normalizedStore]);
          }
        });
      } else {
        console.log('No data_store_types found for model:', model.model_name, 'Value:', model.data_store_types);
      }

      // Compliance breakdown
      if (model.compliance_requirements && model.compliance_requirements !== null && model.compliance_requirements.trim() !== '') {
        console.log('Processing compliance:', model.compliance_requirements);
        const compliances = model.compliance_requirements.split(',');
        console.log('Split compliances:', compliances);
        compliances.forEach(compliance => {
          const trimmedCompliance = compliance.trim();
          if (trimmedCompliance) {
            // Convert to lowercase to make it case-insensitive
            const normalizedCompliance = trimmedCompliance.toLowerCase();
            complianceBreakdown[normalizedCompliance] = (complianceBreakdown[normalizedCompliance] || 0) + 1;
            console.log(`Compliance "${normalizedCompliance}" count now:`, complianceBreakdown[normalizedCompliance]);
          }
        });
      } else {
        console.log('No compliance_requirements found for model:', model.model_name, 'Value:', model.compliance_requirements);
      }
    });

    console.log('Final analytics calculated:', { // Debug log
      totalModels: modelList.length,
      industryBreakdown,
      dataStoreBreakdown,
      complianceBreakdown
    });

    setAnalytics({
      totalModels: modelList.length,
      industryBreakdown,
      dataStoreBreakdown,
      complianceBreakdown
    });
  };
  
  useEffect(() => { 
    // Check if we're in signup flow
    const signupFlow = localStorage.getItem('signup_flow');
    const signupStep = localStorage.getItem('signup_step');
    const clientId = localStorage.getItem('client_id');
    
    // Set logged in status
    setIsLoggedIn(!!clientId);
    
    // More explicit check: only in signup flow if specifically marked AND no existing client_id
    const newIsSignupFlow = signupFlow === 'in_progress' && signupStep === 'model_registry' && !clientId;
    setIsSignupFlow(newIsSignupFlow);
    
    console.log('ModelInventory - signupFlow:', signupFlow, 'signupStep:', signupStep, 'clientId:', clientId, 'isSignupFlow:', newIsSignupFlow, 'isLoggedIn:', !!clientId);
    console.log('API_BASE_URL_CONNECTOR:', API_BASE_URL_CONNECTOR); // Debug log for API URL
    
    // Test API connection
    const testAPIConnection = async () => {
      try {
        const response = await fetch(`${API_BASE_URL_CONNECTOR}/model-inventory/test-structure`);
        if (response.ok) {
          const data = await response.json();
          console.log('API test successful:', data);
        } else {
          console.log('API test failed:', response.status, response.statusText);
        }
      } catch (error) {
        console.log('API connection error:', error);
      }
    };
    
    testAPIConnection();
    
    // Fetch models only if we have client_id or are not in signup flow
    const client_id = getClientId();
    if (client_id || newIsSignupFlow) {
      fetchModels(); 
    }
  }, []);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleAdd = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setError('');
    
    const client_id = getClientId();
    
    try {
      const res = await fetch(`${API_BASE_URL_CONNECTOR}/model-inventory/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, client_id })
      });
      const data = await res.json();
      if (res.ok) {
        setMessage('Model added successfully!');
        setForm({ 
          model_name: '', 
          model_name_dropdown: '',
          model_name_custom: '',
          provider_name: '', 
          provider_name_dropdown: '',
          provider_name_custom: '',
          weights_location: '', 
          bias_notes: '', 
          description: '',
          industry_use_case: '',
          data_store_types: '',
          compliance_requirements: ''
        });
        fetchModels();
        
        // Switch to view tab after successful add
        setActiveTab('view');
        
        // If in signup flow, complete the process
        if (isSignupFlow) {
          setTimeout(() => {
            setMessage('Model added successfully! Completing signup process...');
            setTimeout(() => {
              completeSignupFlow();
            }, 2000);
          }, 1000);
        }
      } else {
        // Handle error response - ensure it's a string
        let errorMessage = 'Failed to add model.';
        if (data.detail) {
          if (Array.isArray(data.detail)) {
            errorMessage = data.detail.map(e => e.msg || e.message || e).join(' ');
          } else if (typeof data.detail === 'string') {
            errorMessage = data.detail;
          } else if (typeof data.detail === 'object') {
            errorMessage = data.detail.message || JSON.stringify(data.detail);
          }
        }
        setError(errorMessage);
      }
    } catch (error) {
      setError('Error adding model.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (model_id) => {
    try {
      const res = await fetch(`${API_BASE_URL_CONNECTOR}/model-inventory/delete/${model_id}`, { method: 'DELETE' });
      if (res.ok) {
        setMessage('Model deleted successfully!');
        fetchModels();
      } else setError('Failed to delete model.');
    } catch (error) {
      setError('Error deleting model.');
    } finally {
      setShowDeleteModal(false);
      setModelToDelete(null);
    }
  };

  const openDeleteModal = (model_id) => {
    setModelToDelete(model_id);
    setShowDeleteModal(true);
  };

  const closeDeleteModal = () => {
    setShowDeleteModal(false);
    setModelToDelete(null);
  };

  const completeSignupFlow = () => {
    // Clear signup flow state
    localStorage.removeItem('signup_flow');
    localStorage.removeItem('signup_step');
    
    // Show completion message and redirect to login for proper authentication
    setMessage('Signup process completed successfully! Please log in to access your dashboard.');
    setTimeout(() => {
      // Clear signup-related localStorage items
      localStorage.removeItem('signup_full_name');
      localStorage.removeItem('signup_company');
      localStorage.removeItem('signup_industry');
      localStorage.removeItem('signup_country');
      
      navigate('/login');
    }, 3000);
  };

  const skipModelRegistration = () => {
    // Complete signup flow without adding a model
    completeSignupFlow();
  };

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
        {/* Signup Flow Banner - Only show during registration */}
        {isSignupFlow && !isLoggedIn && (
          <div style={{
            background: 'var(--primary-gradient)',
            color: 'var(--primary-foreground)',
            background: 'hsl(0 0% 100%)',
            color: 'hsl(222.2 84% 4.9%)',
            padding: '2rem',
            marginBottom: '2rem',
            borderRadius: '12px',
            textAlign: 'center',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}>
            <h2 style={{ 
              margin: '0 0 0.5rem 0',
              fontSize: '1.75rem',
              fontWeight: '600'
            }}>Step 3 of 3: Model Registry (Optional)</h2>
            <p style={{ 
              margin: 0,
              fontSize: '1.1rem',
              opacity: 0.9
            }}>
              Register your custom AI models or skip this step to complete your signup process.
            </p>
          </div>
        )}
        
        {/* Header Section */}
        <div style={{
          textAlign: 'center',
          marginBottom: '3rem'
        }}>
          <h1 className="page-title">
            {isSignupFlow ? 'Model Registry' : 'Model Inventory'}
          </h1>
          <p style={{
            fontSize: '1.25rem',
            color: 'hsl(215.4 16.3% 46.9%)',
            margin: 0,
            maxWidth: '600px',
            marginLeft: 'auto',
            marginRight: 'auto'
          }}>
            {isSignupFlow && !isLoggedIn
              ? 'Register your custom AI models with industry and data store tracking to complete your signup process'
              : 'Register and manage your custom AI models with comprehensive tracking of industries, data stores, and compliance requirements'
            }
          </p>
        </div>
        
        {/* Tab Navigation */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          marginBottom: '2rem'
        }}>
          <div style={{
            background: 'hsl(0 0% 100%)',
            borderRadius: '8px',
            padding: '4px',
            border: '1px solid hsl(214.3 31.8% 91.4%)',
            display: 'flex'
          }}>
            <button
              onClick={() => setActiveTab('view')}
              style={{
                padding: '12px 24px',
                border: 'none',
                borderRadius: '6px',
                backgroundColor: activeTab === 'view' ? 'var(--primary)' : 'transparent',
                color: activeTab === 'view' ? 'var(--primary-foreground)' : 'var(--foreground)',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                fontSize: '14px'
              }}
            >
              View Models
            </button>
            <button
              onClick={() => setActiveTab('add')}
              style={{
                padding: '12px 24px',
                border: 'none',
                borderRadius: '6px',
                backgroundColor: activeTab === 'add' ? 'var(--primary)' : 'transparent',
                color: activeTab === 'add' ? 'var(--primary-foreground)' : 'var(--foreground)',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                fontSize: '14px'
              }}
            >
              Add Model
            </button>
          </div>
        </div>

        {/* Messages */}
        {message && (
          <div style={{
            background: 'var(--primary)',
            color: 'var(--primary-foreground)',
            padding: '1rem 1.5rem',
            borderRadius: '12px',
            marginBottom: '2rem',
            textAlign: 'center',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            border: '1px solid rgba(255, 255, 255, 0.1)'
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
            marginBottom: '2rem',
            textAlign: 'center',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}>
            {error}
          </div>
        )}

        {/* Tab Content */}
        {activeTab === 'view' && (
          <div>
            {/* Info Section for View Tab */}
            <div style={{ 
              background: 'rgba(255, 255, 255, 0.9)',
              backdropFilter: 'blur(10px)',
              padding: '1.5rem', 
              borderRadius: '12px', 
              marginBottom: '2rem',
              textAlign: 'center',
              border: '1px solid rgba(226, 232, 240, 0.5)',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)'
            }}>
              <p style={{ 
                margin: 0, 
                color: '#475569',
                fontSize: '1.1rem'
              }}>
                <strong style={{ color: 'var(--primary) ' }}>Model Overview</strong> - View and manage your registered AI models with analytics and detailed information.
              </p>
            </div>
            
            {/* Analytics Dashboard - Only show when there are models */}
            {models.length > 0 && (
              <div style={{
                background: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(10px)',
                padding: '2.5rem',
                borderRadius: '16px',
                marginBottom: '3rem',
                border: '1px solid rgba(226, 232, 240, 0.5)',
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
              }}>
                <h2 style={{
                  fontSize: '1.875rem',
                  fontWeight: '700',
                  color: '#1f2937',
                  marginBottom: '2rem',
                  textAlign: 'center'
                }}>
                  Model Analytics & Usage
                </h2>
                
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                  gap: '2rem'
                }}>
                  {/* Industry Breakdown */}
                  <div style={{
                    background: '#f8fafc',
                    padding: '1.5rem',
                    borderRadius: '12px',
                    border: '1px solid #e5e7eb'
                  }}>
                    <h3 style={{
                      fontSize: '1.25rem',
                      fontWeight: '600',
                      color: '#374151',
                      marginBottom: '1rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem'
                    }}>
                      🏭 Industry Usage
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {Object.entries(analytics.industryBreakdown).map(([industry, count]) => (
                        <div key={industry} style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '0.5rem',
                          background: 'white',
                          borderRadius: '8px'
                        }}>
                          <span style={{ color: '#374151', fontWeight: '500' }}>{industry}</span>
                          <span style={{
                            background: '#dbeafe',
                            color: '#1e40af',
                            padding: '0.25rem 0.75rem',
                            borderRadius: '20px',
                            fontSize: '0.875rem',
                            fontWeight: '600'
                          }}>
                            {count}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Data Store Breakdown */}
                  <div style={{
                    background: '#f0fdf4',
                    padding: '1.5rem',
                    borderRadius: '12px',
                    border: '1px solid #bbf7d0'
                  }}>
                    <h3 style={{
                      fontSize: '1.25rem',
                      fontWeight: '600',
                      color: '#374151',
                      marginBottom: '1rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem'
                    }}>
                      🗄️ Data Store Usage
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {Object.entries(analytics.dataStoreBreakdown).map(([store, count]) => (
                        <div key={store} style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '0.5rem',
                          background: 'white',
                          borderRadius: '8px'
                        }}>
                          <span style={{ color: '#374151', fontWeight: '500' }}>
                            {/* Capitalize first letter of each word for display */}
                            {store.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                          </span>
                          <span style={{
                            background: '#dcfce7',
                            color: '#15803d',
                            padding: '0.25rem 0.75rem',
                            borderRadius: '20px',
                            fontSize: '0.875rem',
                            fontWeight: '600'
                          }}>
                            {count}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Compliance Breakdown */}
                  <div style={{
                    background: '#fefce8',
                    padding: '1.5rem',
                    borderRadius: '12px',
                    border: '1px solid #fde68a'
                  }}>
                    <h3 style={{
                      fontSize: '1.25rem',
                      fontWeight: '600',
                      color: '#374151',
                      marginBottom: '1rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem'
                    }}>
                      🔒 Compliance Requirements
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {Object.entries(analytics.complianceBreakdown).length > 0 ? (
                        Object.entries(analytics.complianceBreakdown).map(([compliance, count]) => (
                          <div key={compliance} style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            padding: '0.5rem',
                            background: 'white',
                            borderRadius: '8px'
                          }}>
                            <span style={{ color: '#374151', fontWeight: '500' }}>
                              {/* Capitalize first letter of each word for display */}
                              {compliance.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                            </span>
                            <span style={{
                              background: '#fef3c7',
                              color: '#d97706',
                              padding: '0.25rem 0.75rem',
                              borderRadius: '20px',
                              fontSize: '0.875rem',
                              fontWeight: '600'
                            }}>
                              {count}
                            </span>
                          </div>
                        ))
                      ) : (
                        <div style={{
                          textAlign: 'center',
                          color: '#6b7280',
                          fontStyle: 'italic',
                          padding: '1rem'
                        }}>
                          No compliance requirements specified
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Models Table Section */}
            <div style={{
              background: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(10px)',
              padding: '2.5rem',
              borderRadius: '16px',
              border: '1px solid rgba(226, 232, 240, 0.5)',
              boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
            }}>
              <h2 style={{ 
                fontSize: '1.875rem',
                fontWeight: '700',
                color: '#1f2937',
                marginBottom: '2rem',
                textAlign: 'center'
              }}>
                Registered Models
              </h2>

              {models.length === 0 ? (
                <div style={{
                  textAlign: 'center',
                  padding: '3rem 2rem',
                  color: '#6b7280',
                  fontSize: '1.125rem'
                }}>
                  <div style={{
                    width: '80px',
                    height: '80px',
                    background: 'linear-gradient(135deg, #e5e7eb 0%, #d1d5db 100%)',
                    borderRadius: '50%',
                    margin: '0 auto 1rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '2rem'
                  }}>
                    📦
                  </div>
                  You haven't added any AI models yet. Use the "Add Model" tab to register your first model.
                </div>
              ) : (
                <div style={{
                  overflowX: 'auto',
                  borderRadius: '12px',
                  border: '1px solid #e5e7eb'
                }}>
                  <table style={{
                    width: '100%',
                    borderCollapse: 'collapse',
                    background: 'white'
                  }}>
                    <thead>
                      <tr style={{
                        background: 'linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%)'
                      }}>
                        <th style={{
                          padding: '1rem',
                          textAlign: 'left',
                          fontWeight: '600',
                          color: '#374151',
                          borderBottom: '2px solid #e5e7eb'
                        }}>Model Name</th>
                        <th style={{
                          padding: '1rem',
                          textAlign: 'left',
                          fontWeight: '600',
                          color: '#374151',
                          borderBottom: '2px solid #e5e7eb'
                        }}>Provider</th>
                        <th style={{
                          padding: '1rem',
                          textAlign: 'left',
                          fontWeight: '600',
                          color: '#374151',
                          borderBottom: '2px solid #e5e7eb'
                        }}>Industry</th>
                        <th style={{
                          padding: '1rem',
                          textAlign: 'left',
                          fontWeight: '600',
                          color: '#374151',
                          borderBottom: '2px solid #e5e7eb'
                        }}>Data Stores</th>
                        <th style={{
                          padding: '1rem',
                          textAlign: 'left',
                          fontWeight: '600',
                          color: '#374151',
                          borderBottom: '2px solid #e5e7eb'
                        }}>Created At</th>
                        <th style={{
                          padding: '1rem',
                          textAlign: 'center',
                          fontWeight: '600',
                          color: '#374151',
                          borderBottom: '2px solid #e5e7eb'
                        }}>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {models.map((m, index) => (
                        <React.Fragment key={m.model_id}>
                          <tr style={{
                            background: index % 2 === 0 ? 'white' : '#f9fafb',
                            transition: 'all 0.2s'
                          }}>
                            <td style={{
                              padding: '1rem',
                              borderBottom: '1px solid #e5e7eb',
                              fontWeight: '500'
                            }}>{m.model_name}</td>
                            <td style={{
                              padding: '1rem',
                              borderBottom: '1px solid #e5e7eb',
                              color: '#6b7280'
                            }}>{m.provider_name || 'N/A'}</td>
                            <td style={{
                              padding: '1rem',
                              borderBottom: '1px solid #e5e7eb',
                              color: '#6b7280'
                            }}>
                              <span style={{
                                background: (m.industry_use_case && m.industry_use_case !== null && m.industry_use_case.trim() !== '') ? 'linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%)' : '#f3f4f6',
                                color: (m.industry_use_case && m.industry_use_case !== null && m.industry_use_case.trim() !== '') ? '#1e40af' : '#6b7280',
                                padding: '0.25rem 0.75rem',
                                borderRadius: '20px',
                                fontSize: '0.875rem',
                                fontWeight: '500'
                              }}>
                                {(m.industry_use_case && m.industry_use_case !== null && m.industry_use_case.trim() !== '') ? m.industry_use_case : 'Not specified'}
                              </span>
                            </td>
                            <td style={{
                              padding: '1rem',
                              borderBottom: '1px solid #e5e7eb',
                              color: '#6b7280',
                              fontSize: '0.875rem'
                            }}>
                              {(m.data_store_types && m.data_store_types !== null && m.data_store_types.trim() !== '') ? (
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                                  {m.data_store_types.split(',').map((store, idx) => {
                                    const trimmedStore = store.trim();
                                    if (!trimmedStore) return null;
                                    return (
                                      <span key={idx} style={{
                                        background: '#f0fdf4',
                                        color: '#15803d',
                                        padding: '0.125rem 0.5rem',
                                        borderRadius: '12px',
                                        fontSize: '0.75rem',
                                        fontWeight: '500'
                                      }}>
                                        {trimmedStore}
                                      </span>
                                    );
                                  })}
                                </div>
                              ) : 'N/A'}
                            </td>
                            <td style={{
                              padding: '1rem',
                              borderBottom: '1px solid #e5e7eb',
                              color: '#6b7280',
                              fontSize: '0.875rem'
                            }}>{m.created_at?.slice(0, 19).replace('T', ' ')}</td>
                            <td style={{
                              padding: '1rem',
                              borderBottom: '1px solid #e5e7eb',
                              textAlign: 'center'
                            }}>
                              <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
                                <button 
                                  onClick={() => setShowDetails(showDetails === m.model_id ? null : m.model_id)}
                                  style={{
                                    padding: '0.5rem 1rem',
                                    background: 'var(--primary)',
                                    color: 'var(--primary-foreground)',
                                    border: 'none',
                                    borderRadius: '8px',
                                    cursor: 'pointer',
                                    fontSize: '0.875rem',
                                    fontWeight: '500',
                                    transition: 'all 0.2s'
                                  }}
                                  onMouseOver={(e) => e.target.style.transform = 'scale(1.05)'}
                                  onMouseOut={(e) => e.target.style.transform = 'scale(1)'}
                                >
                                  {showDetails === m.model_id ? 'Hide' : 'Show'}
                                </button>
                                <button 
                                  onClick={() => openDeleteModal(m.model_id)}
                                  style={{
                                    padding: '0.5rem 1rem',
                                    background: 'var(--destructive)',
                                    color: 'var(--destructive-foreground)',
                                    border: 'none',
                                    borderRadius: '8px',
                                    cursor: 'pointer',
                                    fontSize: '0.875rem',
                                    fontWeight: '500',
                                    transition: 'all 0.2s'
                                  }}
                                  onMouseOver={(e) => e.target.style.transform = 'scale(1.05)'}
                                  onMouseOut={(e) => e.target.style.transform = 'scale(1)'}
                                >
                                  Delete
                                </button>
                              </div>
                            </td>
                          </tr>
                          {showDetails === m.model_id && (
                            <tr>
                              <td colSpan={6} style={{
                                padding: '1.5rem',
                                background: '#f8fafc',
                                borderBottom: '1px solid #e5e7eb'
                              }}>
                                <div style={{
                                  display: 'grid',
                                  gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
                                  gap: '1rem'
                                }}>
                                  <div>
                                    <strong style={{ color: '#374151' }}>Weights Location:</strong>
                                    <p style={{ margin: '0.25rem 0 0 0', color: '#6b7280', wordBreak: 'break-all' }}>
                                      {m.weights_location || 'N/A'}
                                    </p>
                                  </div>
                                  <div>
                                    <strong style={{ color: '#374151' }}>Compliance Requirements:</strong>
                                    <p style={{ margin: '0.25rem 0 0 0', color: '#6b7280' }}>
                                      {(m.compliance_requirements && m.compliance_requirements !== null && m.compliance_requirements.trim() !== '') ? m.compliance_requirements : 'N/A'}
                                    </p>
                                  </div>
                                  <div>
                                    <strong style={{ color: '#374151' }}>Bias Notes:</strong>
                                    <p style={{ margin: '0.25rem 0 0 0', color: '#6b7280' }}>
                                      {m.bias_notes || 'N/A'}
                                    </p>
                                  </div>
                                  <div style={{ gridColumn: '1 / -1' }}>
                                    <strong style={{ color: '#374151' }}>Description:</strong>
                                    <p style={{ margin: '0.25rem 0 0 0', color: '#6b7280' }}>
                                      {m.description || 'N/A'}
                                    </p>
                                  </div>
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'add' && (
          <div>
            {/* Info Section for Add Tab */}
            {isSignupFlow && !isLoggedIn ? (
              <div style={{ 
                background: 'rgba(255, 255, 255, 0.9)',
                backdropFilter: 'blur(10px)',
                padding: '1.5rem', 
                borderRadius: '12px', 
                marginBottom: '2rem',
                textAlign: 'center',
                border: '1px solid rgba(226, 232, 240, 0.5)',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)'
              }}>
                <p style={{ 
                  margin: 0, 
                  color: '#475569',
                  fontSize: '1.1rem'
                }}>
                  <strong style={{ color: '#2563eb' }}>Almost done!</strong> You can register custom AI models for enhanced data protection. This step is optional.
                </p>
              </div>
            ) : (
              <div style={{ 
                background: 'rgba(255, 255, 255, 0.9)',
                backdropFilter: 'blur(10px)',
                padding: '1.5rem', 
                borderRadius: '12px', 
                marginBottom: '2rem',
                textAlign: 'center',
                border: '1px solid rgba(226, 232, 240, 0.5)',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)'
              }}>
                <p style={{ 
                  margin: 0, 
                  color: '#475569',
                  fontSize: '1.1rem'
                }}>
                  <strong style={{color: 'var(--primary) '}}>Add New Model</strong> - Register a new AI model with comprehensive tracking of industries, data stores, and compliance requirements.
                </p>
              </div>
            )}

            {/* Model Registration Form */}
            <div style={{
              background: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(10px)',
              padding: '2.5rem',
              borderRadius: '16px',
              marginBottom: '3rem',
              border: '1px solid rgba(226, 232, 240, 0.5)',
              boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
            }}>
              <h2 style={{
                fontSize: '1.875rem',
                fontWeight: '700',
                color: '#1f2937',
                marginBottom: '2rem',
                textAlign: 'center'
              }}>
                {isSignupFlow && !isLoggedIn ? 'Register Custom Model (Optional)' : 'Register Custom Model'}
              </h2>
              
              <form onSubmit={handleAdd}>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                  gap: '1.5rem',
                  marginBottom: '1.5rem'
                }}>
                  <div>
                    <label style={{
                      display: 'block',
                      fontSize: '0.875rem',
                      fontWeight: '600',
                      color: '#374151',
                      marginBottom: '0.5rem'
                    }}>Model Name *</label>
                    <div>
                      <select 
                        name="model_name_dropdown" 
                        value={form.model_name_dropdown || ''} 
                        onChange={(e) => {
                          const value = e.target.value;
                          if (value === 'custom') {
                            setForm({ ...form, model_name_dropdown: 'custom', model_name: form.model_name_custom || '' });
                          } else {
                            setForm({ ...form, model_name_dropdown: value, model_name: value, model_name_custom: '' });
                          }
                        }}
                        disabled={loading}
                        style={{
                          width: '100%',
                          padding: '0.75rem 1rem',
                          border: '2px solid #e5e7eb',
                          borderRadius: '12px',
                          fontSize: '1rem',
                          outline: 'none',
                          transition: 'all 0.2s',
                          background: '#ffffff',
                          boxSizing: 'border-box',
                          marginBottom: '0.5rem'
                        }}
                        onFocus={(e) => e.target.style.borderColor = '#2563eb'}
                        onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
                      >
                        <option value="">Select Model</option>
                        <option value="ARIMA/SARIMA">ARIMA/SARIMA</option>
                        <option value="Prophet (by Meta)">Prophet (by Meta)</option>
                        <option value="LSTM Networks">LSTM Networks</option>
                        <option value="Exponential Smoothing (ETS)">Exponential Smoothing (ETS)</option>
                        <option value="XGBoost Time Series">XGBoost Time Series</option>
                        <option value="LightGBM Time Series">LightGBM Time Series</option>
                        <option value="DBSCAN">DBSCAN</option>
                        <option value="Hierarchical Clustering">Hierarchical Clustering</option>
                        <option value="Random Forest">Random Forest</option>
                        <option value="SVM">SVM</option>
                        <option value="Neural Networks">Neural Networks</option>
                        <option value="Decision Trees">Decision Trees</option>
                        <option value="custom">Custom</option>
                      </select>
                      {form.model_name_dropdown === 'custom' && (
                        <input
                          type="text"
                          name="model_name_custom"
                          value={form.model_name_custom || ''}
                          onChange={(e) => {
                            const value = e.target.value;
                            setForm({ ...form, model_name_custom: value, model_name: value });
                          }}
                          placeholder="Enter custom model name"
                          required
                          disabled={loading}
                          style={{
                            width: '100%',
                            padding: '0.75rem 1rem',
                            border: '2px solid #e5e7eb',
                            borderRadius: '12px',
                            fontSize: '1rem',
                            outline: 'none',
                            transition: 'all 0.2s',
                            background: '#ffffff',
                            boxSizing: 'border-box'
                          }}
                          onFocus={(e) => e.target.style.borderColor = '#2563eb'}
                          onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
                        />
                      )}
                    </div>
                  </div>
                  
                  <div>
                    <label style={{
                      display: 'block',
                      fontSize: '0.875rem',
                      fontWeight: '600',
                      color: '#374151',
                      marginBottom: '0.5rem'
                    }}>Provider Name</label>
                    <div>
                      <select 
                        name="provider_name_dropdown" 
                        value={form.provider_name_dropdown || ''} 
                        onChange={(e) => {
                          const value = e.target.value;
                          if (value === 'custom') {
                            setForm({ ...form, provider_name_dropdown: 'custom', provider_name: form.provider_name_custom || '' });
                          } else {
                            setForm({ ...form, provider_name_dropdown: value, provider_name: value, provider_name_custom: '' });
                          }
                        }}
                        disabled={loading}
                        style={{
                          width: '100%',
                          padding: '0.75rem 1rem',
                          border: '2px solid #e5e7eb',
                          borderRadius: '12px',
                          fontSize: '1rem',
                          outline: 'none',
                          transition: 'all 0.2s',
                          background: '#ffffff',
                          boxSizing: 'border-box',
                          marginBottom: '0.5rem'
                        }}
                        onFocus={(e) => e.target.style.borderColor = '#2563eb'}
                        onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
                      >
                        <option value="">Select Provider</option>
                        <option value="AWS Forecast">AWS Forecast</option>
                        <option value="Azure ML">Azure ML</option>
                        <option value="Meta Prophet">Meta Prophet</option>
                        <option value="Google Cloud AI">Google Cloud AI</option>
                        <option value="SAS">SAS</option>
                        <option value="SAP Predictive Analytics">SAP Predictive Analytics</option>
                        <option value="TensorFlow">TensorFlow</option>
                        <option value="PyTorch">PyTorch</option>
                        <option value="OpenAI">OpenAI</option>
                        <option value="Hugging Face">Hugging Face</option>
                        <option value="Scikit-learn">Scikit-learn</option>
                        <option value="Apache Spark">Apache Spark</option>
                        <option value="custom">Custom</option>
                      </select>
                      {form.provider_name_dropdown === 'custom' && (
                        <input
                          type="text"
                          name="provider_name_custom"
                          value={form.provider_name_custom || ''}
                          onChange={(e) => {
                            const value = e.target.value;
                            setForm({ ...form, provider_name_custom: value, provider_name: value });
                          }}
                          placeholder="Enter custom provider name"
                          disabled={loading}
                          style={{
                            width: '100%',
                            padding: '0.75rem 1rem',
                            border: '2px solid #e5e7eb',
                            borderRadius: '12px',
                            fontSize: '1rem',
                            outline: 'none',
                            transition: 'all 0.2s',
                            background: '#ffffff',
                            boxSizing: 'border-box'
                          }}
                          onFocus={(e) => e.target.style.borderColor = '#2563eb'}
                          onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
                        />
                      )}
                    </div>
                  </div>

                  <div>
                    <label style={{
                      display: 'block',
                      fontSize: '0.875rem',
                      fontWeight: '600',
                      color: '#374151',
                      marginBottom: '0.5rem'
                    }}>Industry Use Case</label>
                    <select 
                      name="industry_use_case" 
                      value={form.industry_use_case} 
                      onChange={handleChange} 
                      disabled={loading}
                      style={{
                        width: '100%',
                        padding: '0.75rem 1rem',
                        border: '2px solid #e5e7eb',
                        borderRadius: '12px',
                        fontSize: '1rem',
                        outline: 'none',
                        transition: 'all 0.2s',
                        background: '#ffffff',
                        boxSizing: 'border-box'
                      }}
                      onFocus={(e) => e.target.style.borderColor = '#2563eb'}
                      onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
                    >
                      <option value="">Select Industry</option>
                      <option value="Healthcare">Healthcare</option>
                      <option value="Finance">Finance</option>
                      <option value="Retail">Retail</option>
                      <option value="Technology">Technology</option>
                      <option value="Manufacturing">Manufacturing</option>
                      <option value="Education">Education</option>
                      <option value="Government">Government</option>
                      <option value="Media">Media & Entertainment</option>
                      <option value="Automotive">Automotive</option>
                      <option value="Energy">Energy & Utilities</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>
                </div>
                
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                  gap: '1.5rem',
                  marginBottom: '1.5rem'
                }}>
                  <div>
                    <label style={{
                      display: 'block',
                      fontSize: '0.875rem',
                      fontWeight: '600',
                      color: '#374151',
                      marginBottom: '0.5rem'
                    }}>Data Store Types</label>
                    <div style={{
                      border: '2px solid #e5e7eb',
                      borderRadius: '12px',
                      padding: '0.75rem',
                      background: '#ffffff',
                      minHeight: '48px',
                      cursor: 'text'
                    }}>
                      <div style={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '0.5rem',
                        marginBottom: form.data_store_types ? '0.5rem' : '0'
                      }}>
                        {form.data_store_types.split(',').filter(item => item.trim()).map((item, index) => (
                          <span key={index} style={{
                            background: '#dbeafe',
                            color: '#1e40af',
                            padding: '0.25rem 0.5rem',
                            borderRadius: '6px',
                            fontSize: '0.875rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.25rem'
                          }}>
                            {item.trim()}
                            <button
                              type="button"
                              onClick={() => {
                                const items = form.data_store_types.split(',').filter(i => i.trim() !== item.trim());
                                setForm({ ...form, data_store_types: items.join(', ') });
                              }}
                              style={{
                                background: 'none',
                                border: 'none',
                                color: '#1e40af',
                                cursor: 'pointer',
                                fontSize: '0.75rem',
                                padding: '0',
                                lineHeight: '1'
                              }}
                            >
                              ×
                            </button>
                          </span>
                        ))}
                      </div>
                      <div style={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '0.25rem'
                      }}>
                        {['MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'SQLite', 'Oracle', 'SQL Server', 'Cassandra', 'Amazon S3', 'Google Cloud Storage', 'Azure Blob Storage', 'BigQuery', 'Snowflake', 'Elasticsearch', 'Firebase', 'DynamoDB'].map(store => (
                          <button
                            key={store}
                            type="button"
                            disabled={loading || form.data_store_types.split(',').some(item => item.trim().toLowerCase() === store.toLowerCase())}
                            onClick={() => {
                              const currentItems = form.data_store_types ? form.data_store_types.split(',').filter(item => item.trim()) : [];
                              if (!currentItems.some(item => item.trim().toLowerCase() === store.toLowerCase())) {
                                setForm({ ...form, data_store_types: [...currentItems, store].join(', ') });
                              }
                            }}
                            style={{
                              background: form.data_store_types.split(',').some(item => item.trim().toLowerCase() === store.toLowerCase()) ? '#f3f4f6' : '#f8fafc',
                              color: form.data_store_types.split(',').some(item => item.trim().toLowerCase() === store.toLowerCase()) ? '#9ca3af' : '#374151',
                              border: '1px solid #e5e7eb',
                              borderRadius: '6px',
                              padding: '0.25rem 0.5rem',
                              fontSize: '0.75rem',
                              cursor: form.data_store_types.split(',').some(item => item.trim().toLowerCase() === store.toLowerCase()) ? 'not-allowed' : 'pointer',
                              transition: 'all 0.2s'
                            }}
                          >
                            {store}
                          </button>
                        ))}
                      </div>
                      <input
                        type="text"
                        placeholder="Or type custom data store and press Enter"
                        disabled={loading}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            const value = e.target.value.trim();
                            if (value) {
                              const currentItems = form.data_store_types ? form.data_store_types.split(',').filter(item => item.trim()) : [];
                              if (!currentItems.some(item => item.trim().toLowerCase() === value.toLowerCase())) {
                                setForm({ ...form, data_store_types: [...currentItems, value].join(', ') });
                                e.target.value = '';
                              }
                            }
                          }
                        }}
                        style={{
                          width: '100%',
                          border: 'none',
                          outline: 'none',
                          background: 'transparent',
                          fontSize: '0.875rem',
                          marginTop: '0.5rem',
                          color: '#6b7280'
                        }}
                      />
                    </div>
                  </div>

                  <div>
                    <label style={{
                      display: 'block',
                      fontSize: '0.875rem',
                      fontWeight: '600',
                      color: '#374151',
                      marginBottom: '0.5rem'
                    }}>Compliance Requirements</label>
                    <div style={{
                      border: '2px solid #e5e7eb',
                      borderRadius: '12px',
                      padding: '0.75rem',
                      background: '#ffffff',
                      minHeight: '48px',
                      cursor: 'text'
                    }}>
                      <div style={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '0.5rem',
                        marginBottom: form.compliance_requirements ? '0.5rem' : '0'
                      }}>
                        {form.compliance_requirements.split(',').filter(item => item.trim()).map((item, index) => (
                          <span key={index} style={{
                            background: '#dbeafe',
                            color: '#1e40af',
                            padding: '0.25rem 0.5rem',
                            borderRadius: '6px',
                            fontSize: '0.875rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.25rem'
                          }}>
                            {item.trim()}
                            <button
                              type="button"
                              onClick={() => {
                                const items = form.compliance_requirements.split(',').filter(i => i.trim() !== item.trim());
                                setForm({ ...form, compliance_requirements: items.join(', ') });
                              }}
                              style={{
                                background: 'none',
                                border: 'none',
                                color: '#d97706',
                                cursor: 'pointer',
                                fontSize: '0.75rem',
                                padding: '0',
                                lineHeight: '1'
                              }}
                            >
                              ×
                            </button>
                          </span>
                        ))}
                      </div>
                      <div style={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '0.25rem'
                      }}>
                        {['GDPR', 'HIPAA', 'SOX', 'PCI-DSS', 'CCPA', 'FERPA', 'GLBA', 'ISO 27001', 'SOC 2', 'FISMA', 'PIPEDA', 'LGPD'].map(compliance => (
                          <button
                            key={compliance}
                            type="button"
                            disabled={loading || form.compliance_requirements.split(',').some(item => item.trim().toLowerCase() === compliance.toLowerCase())}
                            onClick={() => {
                              const currentItems = form.compliance_requirements ? form.compliance_requirements.split(',').filter(item => item.trim()) : [];
                              if (!currentItems.some(item => item.trim().toLowerCase() === compliance.toLowerCase())) {
                                setForm({ ...form, compliance_requirements: [...currentItems, compliance].join(', ') });
                              }
                            }}
                            style={{
                              background: form.compliance_requirements.split(',').some(item => item.trim().toLowerCase() === compliance.toLowerCase()) ? '#f3f4f6' : '#f8fafc',
                              color: form.compliance_requirements.split(',').some(item => item.trim().toLowerCase() === compliance.toLowerCase()) ? '#9ca3af' : '#374151',
                              border: '1px solid #e5e7eb',
                              borderRadius: '6px',
                              padding: '0.25rem 0.5rem',
                              fontSize: '0.75rem',
                              cursor: form.compliance_requirements.split(',').some(item => item.trim().toLowerCase() === compliance.toLowerCase()) ? 'not-allowed' : 'pointer',
                              transition: 'all 0.2s'
                            }}
                          >
                            {compliance}
                          </button>
                        ))}
                      </div>
                      <input
                        type="text"
                        placeholder="Or type custom compliance requirement and press Enter"
                        disabled={loading}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            const value = e.target.value.trim();
                            if (value) {
                              const currentItems = form.compliance_requirements ? form.compliance_requirements.split(',').filter(item => item.trim()) : [];
                              if (!currentItems.some(item => item.trim().toLowerCase() === value.toLowerCase())) {
                                setForm({ ...form, compliance_requirements: [...currentItems, value].join(', ') });
                                e.target.value = '';
                              }
                            }
                          }
                        }}
                        style={{
                          width: '100%',
                          border: 'none',
                          outline: 'none',
                          background: 'transparent',
                          fontSize: '0.875rem',
                          marginTop: '0.5rem',
                          color: '#6b7280'
                        }}
                      />
                    </div>
                  </div>
                </div>
                
                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    color: '#374151',
                    marginBottom: '0.5rem'
                  }}>Weights Location (URL or path)</label>
                  <input 
                    name="weights_location" 
                    value={form.weights_location} 
                    onChange={handleChange} 
                    placeholder="e.g., https://your-domain.com/model.h5" 
                    disabled={loading}
                    style={{
                      width: '100%',
                      padding: '0.75rem 1rem',
                      border: '2px solid #e5e7eb',
                      borderRadius: '12px',
                      fontSize: '1rem',
                      outline: 'none',
                      transition: 'all 0.2s',
                      background: '#ffffff',
                      boxSizing: 'border-box'
                    }}
                    onFocus={(e) => e.target.style.borderColor = '#2563eb'}
                    onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
                  />
                </div>
                
                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    color: '#374151',
                    marginBottom: '0.5rem'
                  }}>Bias Notes</label>
                  <div style={{
                    border: '2px solid #e5e7eb',
                    borderRadius: '12px',
                    padding: '0.75rem',
                    background: '#ffffff',
                    minHeight: '48px',
                    cursor: 'text'
                  }}>
                    <div style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '0.5rem',
                      marginBottom: form.bias_notes ? '0.5rem' : '0'
                    }}>
                      {form.bias_notes.split(',').filter(item => item.trim()).map((item, index) => (
                        <span key={index} style={{
                          background: '#dbeafe',
                          color: '#1e40af',
                          padding: '0.25rem 0.5rem',
                          borderRadius: '6px',
                          fontSize: '0.875rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.25rem'
                        }}>
                          {item.trim()}
                          <button
                            type="button"
                            onClick={() => {
                              const items = form.bias_notes.split(',').filter(i => i.trim() !== item.trim());
                              setForm({ ...form, bias_notes: items.join(', ') });
                            }}
                            style={{
                              background: 'none',
                              border: 'none',
                              color: '#1e40af',
                              cursor: 'pointer',
                              fontSize: '0.75rem',
                              padding: '0',
                              lineHeight: '1'
                            }}
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                    <div style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '0.25rem'
                    }}>
                      {['Sampling Bias', 'Measurement Bias', 'Historical Bias', 'Confirmation Bias', 'Label Bias', 'Observer Bias', 'Prejudice Bias', 'Algorithmic Bias', 'Selection Bias', 'Gender Bias', 'Racial Bias', 'Age Bias'].map(bias => (
                        <button
                          key={bias}
                          type="button"
                          disabled={loading || form.bias_notes.split(',').some(item => item.trim().toLowerCase() === bias.toLowerCase())}
                          onClick={() => {
                            const currentItems = form.bias_notes ? form.bias_notes.split(',').filter(item => item.trim()) : [];
                            if (!currentItems.some(item => item.trim().toLowerCase() === bias.toLowerCase())) {
                              const newItems = [...currentItems, bias];
                              setForm({ ...form, bias_notes: newItems.join(', ') });
                            }
                          }}
                          style={{
                            background: form.bias_notes.split(',').some(item => item.trim().toLowerCase() === bias.toLowerCase()) ? '#f3f4f6' : '#f8fafc',
                            color: form.bias_notes.split(',').some(item => item.trim().toLowerCase() === bias.toLowerCase()) ? '#9ca3af' : '#374151',
                            border: '1px solid #e5e7eb',
                            borderRadius: '6px',
                            padding: '0.25rem 0.5rem',
                            fontSize: '0.75rem',
                            cursor: form.bias_notes.split(',').some(item => item.trim().toLowerCase() === bias.toLowerCase()) ? 'not-allowed' : 'pointer',
                            transition: 'all 0.2s'
                          }}
                        >
                          {bias}
                        </button>
                      ))}
                    </div>
                    <input
                      type="text"
                      placeholder="Or type custom bias note and press Enter"
                      disabled={loading}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          const value = e.target.value.trim();
                          if (value) {
                            const currentItems = form.bias_notes ? form.bias_notes.split(',').filter(item => item.trim()) : [];
                            if (!currentItems.some(item => item.trim().toLowerCase() === value.toLowerCase())) {
                              const newItems = [...currentItems, value];
                              setForm({ ...form, bias_notes: newItems.join(', ') });
                              e.target.value = '';
                            }
                          }
                        }
                      }}
                      style={{
                        width: '100%',
                        border: 'none',
                        outline: 'none',
                        background: 'transparent',
                        fontSize: '0.875rem',
                        marginTop: '0.5rem',
                        color: '#6b7280'
                      }}
                    />
                  </div>
                </div>
                
                <div style={{ marginBottom: '2rem' }}>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    color: '#374151',
                    marginBottom: '0.5rem'
                  }}>Description</label>
                  <textarea 
                    name="description" 
                    value={form.description} 
                    onChange={handleChange} 
                    placeholder="Provide a detailed description of the model, its purpose, and its limitations."
                    disabled={loading}
                    rows={4}
                    style={{
                      width: '100%',
                      padding: '0.75rem 1rem',
                      border: '2px solid #e5e7eb',
                      borderRadius: '12px',
                      fontSize: '1rem',
                      outline: 'none',
                      transition: 'all 0.2s',
                      background: '#ffffff',
                      boxSizing: 'border-box',
                      resize: 'vertical'
                    }}
                    onFocus={(e) => e.target.style.borderColor = '#2563eb'}
                    onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
                  />
                </div>
                
                <button 
                  type="submit" 
                  disabled={loading}
                  style={{
                    width: '100%',
                    background: loading ? 'var(--muted)' : 'var(--primary)',
                    color: loading ? 'var(--muted-foreground)' : 'var(--primary-foreground)',
                    padding: '1rem 2rem',
                    border: 'none',
                    borderRadius: '12px',
                    fontSize: '1.1rem',
                    fontWeight: '600',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    transition: 'all 0.2s',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                  onMouseOver={(e) => !loading && (e.target.style.transform = 'translateY(-2px)')}
                  onMouseOut={(e) => !loading && (e.target.style.transform = 'translateY(0)')}
                >
                  {loading 
                    ? 'Adding Model...' 
                    : (isSignupFlow && !isLoggedIn)
                      ? 'Add Model & Continue' 
                      : 'Add Model'
                  }
                </button>
              </form>
            </div>
          </div>
        )}

        {/* Action Controls - Different for signup vs logged in */}
        {isSignupFlow && !isLoggedIn ? (
          <div style={{ 
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
            marginTop: '2rem', 
            padding: '2rem', 
            borderRadius: '20px', 
            border: '2px solid hsl(220 13% 91%)',
            textAlign: 'center',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
          }}>
            <h3 style={{ 
              color: 'hsl(222.2 84% 4.9%)', 
              marginBottom: '1rem',
              fontSize: '1.5rem',
              fontWeight: '700'
            }}>
              Complete Your Signup Process
            </h3>
            <p style={{ 
              marginBottom: '2rem', 
              color: '#475569',
              fontSize: '1.1rem'
            }}>
              You can add a custom AI model now or skip this step and complete your registration.
            </p>
            <div style={{ 
              display: 'flex', 
              gap: '1rem', 
              justifyContent: 'center', 
              flexWrap: 'wrap' 
            }}>
              <button 
                type="button" 
                onClick={() => navigate('/sde-catalogue')}
                style={{
                  padding: '0.875rem 2rem',
                  background: 'var(--secondary)',
                  color: 'var(--secondary-foreground)',
                  border: 'none',
                  borderRadius: '12px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  fontSize: '1rem',
                  transition: 'all 0.2s',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
                onMouseOver={(e) => e.target.style.transform = 'translateY(-2px)'}
                onMouseOut={(e) => e.target.style.transform = 'translateY(0)'}
              >
                ← Back to SDE Catalogue
              </button>
              <button 
                type="button" 
                onClick={skipModelRegistration}
                style={{
                  padding: '0.875rem 2rem',
                  background: 'var(--primary)',
                  color: 'var(--primary-foreground)',
                  border: 'none',
                  borderRadius: '12px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  fontSize: '1rem',
                  transition: 'all 0.2s',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
                onMouseOver={(e) => e.target.style.transform = 'translateY(-2px)'}
                onMouseOut={(e) => e.target.style.transform = 'translateY(0)'}
              >
                Skip & Complete Signup
              </button>
            </div>
          </div>
        ) : (
          <div style={{ 
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
            marginTop: '2rem', 
            padding: '2rem', 
            borderRadius: '16px', 
            border: '1px solid rgba(226, 232, 240, 0.5)',
            textAlign: 'center',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
          }}>
            <div style={{ 
              display: 'flex', 
              gap: '1rem', 
              justifyContent: 'center', 
              flexWrap: 'wrap' 
            }}>
              <button 
                type="button" 
                onClick={() => navigate('/dashboard')}
                style={{
                  padding: '0.875rem 2rem',
                  background: 'var(--primary)',
                  color: 'var(--primary-foreground)',
                  border: 'none',
                  borderRadius: '12px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  fontSize: '1rem',
                  transition: 'all 0.2s',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
                onMouseOver={(e) => e.target.style.transform = 'translateY(-2px)'}
                onMouseOut={(e) => e.target.style.transform = 'translateY(0)'}
              >
                Return to Dashboard
              </button>
              <button 
                type="button" 
                onClick={() => navigate('/connect')}
                style={{
                  padding: '0.875rem 2rem',
                  background: 'var(--accent)',
                  color: 'var(--accent-foreground)',
                  border: 'none',
                  borderRadius: '12px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  fontSize: '1rem',
                  transition: 'all 0.2s',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
                onMouseOver={(e) => e.target.style.transform = 'translateY(-2px)'}
                onMouseOut={(e) => e.target.style.transform = 'translateY(0)'}
              >
                Connect Data Sources
              </button>
            </div>
          </div>
        )}

        {/* Custom Modal for Delete Confirmation */}
        {showDeleteModal && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
          }}>
            <div style={{
              background: 'white',
              padding: '2rem',
              borderRadius: '16px',
              maxWidth: '400px',
              width: '90%',
              textAlign: 'center',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
            }}>
              <h3 style={{
                fontSize: '1.25rem',
                fontWeight: '700',
                color: '#1f2937',
                marginBottom: '1rem'
              }}>Confirm Deletion</h3>
              <p style={{
                color: '#6b7280',
                marginBottom: '2rem'
              }}>Are you sure you want to delete this model? This action cannot be undone.</p>
              <div style={{
                display: 'flex',
                gap: '1rem',
                justifyContent: 'center'
              }}>
                <button 
                  onClick={closeDeleteModal}
                  style={{
                    padding: '0.75rem 1.5rem',
                    background: 'var(--secondary)',
                    color: 'var(--secondary-foreground)',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '500',
                    transition: 'all 0.2s'
                  }}
                >
                  Cancel
                </button>
                <button 
                  onClick={() => handleDelete(modelToDelete)}
                  style={{
                    padding: '0.75rem 1.5rem',
                    background: 'var(--destructive)',
                    color: 'var(--destructive-foreground)',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '500',
                    transition: 'all 0.2s'
                  }}
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ModelInventoryPage;
