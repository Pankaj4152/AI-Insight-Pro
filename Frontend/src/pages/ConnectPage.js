import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL_CONNECTOR, API_BASE_URL_DRIVER } from '../apiConfig';
import '../Css/Connect.css';

// Reusable Form Component - Now handles individual steps
const DynamicForm = ({
  selectedSource, onInputChange, formData, validationErrors, onFileChange, fileInputRef, currentStep, onFormSubmit, onNextStep, onPreviousStep, isLastStep, onTestConnection, testStatus, getTypeValue, getServiceValue, submitEnabled,
  validateStep, totalSteps, setSubmissionMessage, setConnections, setFormData, setSelectedSource, setCurrentStep, setTestStatus, setShowToast, runDiscovery, getPlaceholders
}) => {
  // Function to count words for description
  const countWords = (text) => {
    return text.trim().split(/\s+/).filter(word => word.length > 0).length;
  };

  const renderStepContent = () => {
    const placeholders = getPlaceholders();
    
    switch (currentStep) {
      case 1: // Basic Connection Details
        return (
          <>
            <div className="form-group">
              <label htmlFor="name">Name:<span className="required-asterisk">*</span></label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name || ''}
                onChange={onInputChange}
                placeholder={placeholders.name || 'Enter connection name'}
                required
                className="form-input"
              />
              {validationErrors.name && <p className="error-message">{validationErrors.name}</p>}
            </div>
            <div className="form-group">
              <label htmlFor="type">Type:</label>
              <input
                type="text"
                id="type"
                name="type"
                value={getTypeValue()}
                readOnly
                disabled
                className="form-input disabled"
              />
            </div>
            <div className="form-group">
              <label htmlFor="service">Service:</label>
              <input
                type="text"
                id="service"
                name="service"
                value={getServiceValue()}
                readOnly
                disabled
                className="form-input disabled"
              />
            </div>
            {(selectedSource === 'bigquery' || selectedSource === 'gcp-bucket') && (
              <>
                <div className="form-group">
                  <label htmlFor="projectId">Project ID:<span className="required-asterisk">*</span></label>
                  <input
                    type="text"
                    id="projectId"
                    name="projectId"
                    value={formData.projectId || ''}
                    onChange={onInputChange}
                    placeholder={placeholders.projectId || 'Enter GCP project ID'}
                    required
                    className="form-input"
                  />
                  {validationErrors.projectId && <p className="error-message">{validationErrors.projectId}</p>}
                </div>
                <div className="form-group">
                  <label htmlFor="datasetId">
                    {selectedSource === 'gcp-bucket' ? 'Bucket Name' : 'Dataset ID'}<span className="required-asterisk">*</span>
                  </label>
                  <input
                    type="text"
                    id="datasetId"
                    name="datasetId"
                    value={formData.datasetId || ''}
                    onChange={onInputChange}
                    placeholder={placeholders.datasetId || (selectedSource === 'gcp-bucket' ? 'Enter bucket name' : 'Enter dataset ID')}
                    required
                    className="form-input"
                  />
                  {validationErrors.datasetId && <p className="error-message">{validationErrors.datasetId}</p>}
                </div>
              </>
            )}
            {(selectedSource === 'mysql' || selectedSource === 'postgresql') && (
              <>
                <div className="form-group">
                  <label htmlFor="host">Host / IP Address:<span className="required-asterisk">*</span></label>
                  <input
                    type="text"
                    id="host"
                    name="host"
                    value={formData.host || ''}
                    onChange={onInputChange}
                    placeholder={placeholders.host || 'Enter host or IP address'}
                    required
                    className="form-input"
                  />
                  {validationErrors.host && <p className="error-message">{validationErrors.host}</p>}
                </div>
                <div className="form-group">
                  <label htmlFor="port">Port:<span className="required-asterisk">*</span></label>
                  <input
                    type="number"
                    id="port"
                    name="port"
                    value={formData.port || ''}
                    onChange={onInputChange}
                    placeholder={placeholders.port || (selectedSource === 'postgresql' ? '5432' : '3306')}
                    required
                    className="form-input"
                  />
                  {validationErrors.port && <p className="error-message">{validationErrors.port}</p>}
                </div>
              </>
            )}
          </>
        );
      case 2: // Credentials and Authentication
        return (
          <>
            {(selectedSource === 'bigquery' || selectedSource === 'gcp-bucket') && (
              <div className="form-group">
                <label htmlFor="credentialFile">Upload Credential File:<span className="required-asterisk">*</span></label>
                <input
                  type="file"
                  id="credentialFile"
                  name="credentialFile"
                  accept=".json"
                  onChange={onFileChange}
                  ref={fileInputRef}
                  required
                  className="form-input-file"
                />
                {validationErrors.credentialFile && (
                  <p className="error-message">{validationErrors.credentialFile}</p>
                )}
                {formData.credentialFileName && (
                  <p className="file-name-display">Selected: {formData.credentialFileName}</p>
                )}
                <div className="security-notice warning">
                  <p>
                    Credential files contain sensitive information. They will be securely stored and encrypted at rest.
                    Do not share this file publicly.
                  </p>
                </div>
              </div>
            )}

            {(selectedSource === 'mysql' || selectedSource === 'postgresql') && (
              <>
                <div className="form-group">
                  <label htmlFor={selectedSource === 'mysql' ? "databaseName" : "database"}>Database Name:<span className="required-asterisk">*</span></label>
                  <input
                    type="text"
                    id={selectedSource === 'mysql' ? "databaseName" : "database"}
                    name={selectedSource === 'mysql' ? "databaseName" : "database"}
                    value={formData[selectedSource === 'mysql' ? "databaseName" : "database"] || ''}
                    onChange={onInputChange}
                    placeholder={selectedSource === 'mysql' ? placeholders.databaseName : placeholders.database || 'Enter database name'}
                    required
                    className="form-input"
                  />
                  {validationErrors[selectedSource === 'mysql' ? "databaseName" : "database"] && <p className="error-message">{validationErrors[selectedSource === 'mysql' ? "databaseName" : "database"]}</p>}
                </div>
                <div className="form-group">
                  <label htmlFor="username">Username:<span className="required-asterisk">*</span></label>
                  <input
                    type="text"
                    id="username"
                    name="username"
                    value={formData.username || ''}
                    onChange={onInputChange}
                    placeholder={placeholders.username || 'Enter username'}
                    required
                    className="form-input"
                  />
                  {validationErrors.username && <p className="error-message">{validationErrors.username}</p>}
                </div>
                <div className="form-group">
                  <label htmlFor="password">Password:<span className="required-asterisk">*</span></label>
                  <input
                    type="password"
                    id="password"
                    name="password"
                    value={formData.password || ''}
                    onChange={onInputChange}
                    placeholder={placeholders.password || 'Enter password'}
                    required
                    className="form-input"
                  />
                  {validationErrors.password && <p className="error-message">{validationErrors.password}</p>}
                  <div className="security-notice info">
                    <p>
                      Passwords are encrypted at rest and in transit. We follow industry best practices for credential handling.
                    </p>
                  </div>
                </div>
              </>
            )}
            <button type="button" onClick={onTestConnection} className="test-connection-button" disabled={testStatus === 'testing'}>
              {testStatus === 'testing' ? 'Testing...' : 'Test Connection'}
            </button>
            {testStatus === 'success' && <p className="test-status success">Connection successful!</p>}
            {testStatus === 'failed' && <p className="test-status error">Connection failed. Please check credentials.</p>}
          </>
        );
      case 3: // Advanced Settings (PostgreSQL) and Description
        return (
          <>
            {/* Description field always on the last step for BigQuery/GCP */}
            {(selectedSource === 'bigquery' || selectedSource === 'gcp-bucket') && (
              <div className="form-group">
                <label htmlFor="description">Description:</label>
                <textarea
                  id="description"
                  name="description"
                  value={formData.description || ''}
                  onChange={onInputChange}
                  placeholder={placeholders.description || 'Optional: Brief description of this connection'}
                  maxLength={50 * 7} // Max 50 words, roughly 350 chars
                  className="form-textarea"
                ></textarea>
                <p className="word-count">
                  {countWords(formData.description || '')} / 50 words
                  {validationErrors.description && (
                    <span className="error-message"> ({validationErrors.description})</span>
                  )}
                </p>
              </div>
            )}
          </>
        );
      default:
        return null;
    }
  };

  return (
    <form onSubmit={onFormSubmit} className="dynamic-form">
      {renderStepContent()}
      <div className="form-navigation">
        {currentStep > 1 && (
          <button type="button" onClick={onPreviousStep} className="nav-button prev-button">
            Previous
          </button>
        )}
        {!isLastStep ? (
          <button type="button" onClick={onNextStep} className="nav-button next-button">
            Next
          </button>
        ) : (
          <div className="submit-buttons-container">
            <button
              type="submit"
              className={`submit-button ${testStatus === 'failed' ? 'retry-button' : ''}`}
              disabled={!submitEnabled}
              onClick={e => {
                if (!submitEnabled) {
                  e.preventDefault();
                  // Do nothing if not enabled
                  return;
                }
                // Only run discovery if enabled and clicked
                e.preventDefault();
                if (validateStep(totalSteps)) {
                  if (testStatus !== 'success') {
                    setSubmissionMessage('Please test the connection and ensure it is successful before submitting.');
                    return;
                  }
                  const newConnection = {
                    id: Date.now(),
                    name: formData.name,
                    type: getTypeValue(),
                    service: getServiceValue(),
                    status: 'Connected',
                    dateAdded: new Date().toLocaleString(),
                    displayData: { ...formData }
                  };
                  delete newConnection.displayData.password;
                  delete newConnection.displayData.credentialFile;
                  setConnections(prev => [...prev, newConnection]);
                  setSubmissionMessage('Data source connected successfully!');
                  setFormData({});
                  setSelectedSource('');
                  setCurrentStep(1);
                  setTestStatus('idle');
                  if (fileInputRef.current) {
                    fileInputRef.current.value = '';
                  }
                  setShowToast(true);
                  setTimeout(() => setShowToast(false), 2000);
                  // Run discovery after connection is saved
                  const user = JSON.parse(localStorage.getItem('user')) || {};
                  const clientIdFromLogin = user.client_id || localStorage.getItem('client_id');
                  if (clientIdFromLogin) {
                    runDiscovery(clientIdFromLogin);
                  }
                } else {
                  setSubmissionMessage('Please correct the errors before submitting.');
                }
              }}
            >
              {testStatus === 'failed' ? 'Retry' : 'Submit and Discover'}
            </button>
            {testStatus === 'failed' && (
              <button
                type="button"
                className="cancel-button"
                onClick={() => {
                  window.location.reload();
                }}
              >
                Cancel
              </button>
            )}
          </div>
        )}
      </div>
    </form>
  );
};

function ConnectPage() {
  const navigate = useNavigate();
  const [selectedSource, setSelectedSource] = useState('');
  const [formData, setFormData] = useState({});
  const [validationErrors, setValidationErrors] = useState({});
  const [submissionMessage, setSubmissionMessage] = useState('');
  const [currentStep, setCurrentStep] = useState(1);
  const [testStatus, setTestStatus] = useState('idle'); // 'idle', 'testing', 'success', 'failed'
  const [connections, setConnections] = useState([]); // For connection history
  const fileInputRef = useRef(null);
  const [showToast, setShowToast] = useState(false);
  const [connectionHistory, setConnectionHistory] = useState([]);
  const [discoveryProgress, setDiscoveryProgress] = useState(0);
  const [discoveryRunning, setDiscoveryRunning] = useState(false);

  // Helper functions moved to ConnectPage
  const getTypeValue = () => {
    if (selectedSource === 'bigquery') return 'BigQuery';
    if (selectedSource === 'gcp-bucket') return 'GCP';
    if (selectedSource === 'postgresql') return 'Database';
    if (selectedSource === 'mysql') return 'Database';
    return '';
  };

  const getServiceValue = () => {
    if (selectedSource === 'bigquery') return 'BigQuery';
    if (selectedSource === 'gcp-bucket') return 'GCP Bucket';
    if (selectedSource === 'postgresql') return 'PostgreSQL';
    if (selectedSource === 'mysql') return 'MySQL';
    return '';
  };

  // Define total steps based on selected source
  const getTotalSteps = () => {
    if (selectedSource === 'bigquery' || selectedSource === 'gcp-bucket') {
      return 2; // Step 1: Name, Project/Dataset; Step 2: Credential, Description
    } else if (selectedSource === 'mysql' || selectedSource === 'postgresql') {
      return 2; // Step 1: Name, Host, Port; Step 2: DB Name, User, Pass
    }
    return 0;
  };

  const totalSteps = getTotalSteps();
  const isLastStep = currentStep === totalSteps;

  // Load data from localStorage on component mount
  useEffect(() => {
    const savedData = localStorage.getItem('connectFormData');
    if (savedData) {
      const parsedData = JSON.parse(savedData);
      setFormData(parsedData.formData || {});
      setSelectedSource(parsedData.selectedSource || '');
      setCurrentStep(parsedData.currentStep || 1);
    }
    const savedConnections = localStorage.getItem('connections');
    if (savedConnections) {
      setConnections(JSON.parse(savedConnections));
    }

    const connectContainer = document.getElementById('connect-container');
    if (connectContainer) {
      connectContainer.classList.add('fade-in');
    }

    // Fetch connection history for this client
    const user = JSON.parse(localStorage.getItem('user')) || {};
    const client_id = user.client_id || localStorage.getItem('client_id');
    if (client_id) {
      fetch(`${API_BASE_URL_CONNECTOR}/connection-history/${client_id}`)
        .then(res => res.json())
        .then(data => setConnectionHistory(data.history || []));
    }
  }, []);

  // Update localStorage whenever relevant state changes
  useEffect(() => {
    const dataToStore = {
      selectedSource,
      formData,
      currentStep
    };
    localStorage.setItem('connectFormData', JSON.stringify(dataToStore));
    localStorage.setItem('connections', JSON.stringify(connections));
  }, [formData, selectedSource, currentStep, connections]);



  const validateStep = (step) => {
    let errors = {};
    let isValid = true;

    if (step === 1) {
      if (!formData.name) { errors.name = 'Name is required.'; isValid = false; }

      if (selectedSource === 'bigquery' || selectedSource === 'gcp-bucket') {
        if (!formData.projectId) { errors.projectId = 'Project ID is required.'; isValid = false; }
        if (!formData.datasetId) { errors.datasetId = 'Dataset ID is required.'; isValid = false; }
      } else if (selectedSource === 'mysql' || selectedSource === 'postgresql') {
        if (!formData.host) { errors.host = 'Host / IP Address is required.'; isValid = false; }
        if (!formData.port) { errors.port = 'Port is required.'; isValid = false; }
      }
    } else if (step === 2) {
      if (selectedSource === 'bigquery' || selectedSource === 'gcp-bucket') {
        if (!formData.credentialFile) { errors.credentialFile = 'Credential file is required.'; isValid = false; }
        else if (formData.credentialFile && !formData.credentialFile.name.endsWith('.json')) {
          errors.credentialFile = 'Credential file must be a .json file.'; isValid = false;
        }
      } else if (selectedSource === 'mysql' || selectedSource === 'postgresql') {
        if (!formData.databaseName && selectedSource === 'mysql') { errors.databaseName = 'Database Name is required.'; isValid = false; }
        if (!formData.database && selectedSource === 'postgresql') { errors.database = 'Database Name is required.'; isValid = false; }
        if (!formData.username) { errors.username = 'Username is required.'; isValid = false; }
        if (!formData.password) { errors.password = 'Password is required.'; isValid = false; }
      }
    } else if (step === 3) {
      // Only PostgreSQL has a third step with optional fields, no strict validation needed unless specific rules apply
      if ((selectedSource === 'bigquery' || selectedSource === 'gcp-bucket') && formData.description) {
        const wordCount = formData.description.trim().split(/\s+/).filter(word => word.length > 0).length;
        if (wordCount > 50) {
          errors.description = 'Description cannot exceed 50 words.'; isValid = false;
        }
      }
    }

    setValidationErrors(errors);
    return isValid;
  };

  const handleNextStep = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, totalSteps));
      setSubmissionMessage(''); // Clear submission message on step change
      setTestStatus('idle'); // Reset test status on step change
    } else {
      setSubmissionMessage('Please correct the errors before proceeding.');
    }
  };

  const handlePreviousStep = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
    setSubmissionMessage(''); // Clear submission message on step change
    setTestStatus('idle'); // Reset test status on step change
  };

  // Helper: which fields are core connection fields for each source
  const coreFields = {
    mysql: ["host", "port", "databaseName", "username", "password"],
    postgresql: ["host", "port", "database", "username", "password"],
    bigquery: ["projectId", "datasetId", "credentialFile"],
    "gcp-bucket": ["projectId", "datasetId", "credentialFile"],
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Only reset testStatus if a core connection field is changed
    if (coreFields[selectedSource] && coreFields[selectedSource].includes(name)) {
      setTestStatus('idle');
    }
    // Clear specific error message as user types
    setValidationErrors(prev => {
      const newErrors = { ...prev };
      if (newErrors[name]) {
        delete newErrors[name];
      }
      return newErrors;
    });
    setSubmissionMessage(''); // Clear submission message on input change
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setFormData(prev => ({ ...prev, credentialFile: file, credentialFileName: file ? file.name : '' }));
    setValidationErrors(prev => {
      const newErrors = { ...prev };
      if (newErrors.credentialFile) {
        delete newErrors.credentialFile;
      }
      return newErrors;
    });
    setSubmissionMessage('');
    setTestStatus('idle');
  };

  const handleTestConnection = async () => {
    if (!validateStep(currentStep)) {
      setSubmissionMessage('Please fill in required fields before testing connection.');
      setTestStatus('failed');
      return;
    }

    setTestStatus('testing');
    setSubmissionMessage('');

    try {
      let response;
      const user = JSON.parse(localStorage.getItem('user')) || {};
      const clientIdFromLogin = user.client_id || localStorage.getItem('client_id');

      if (selectedSource === 'mysql') {
        const requestData = new URLSearchParams();
        requestData.append('host', formData.host);
        requestData.append('port', Number(formData.port));
        requestData.append('databaseName', formData.databaseName);
        requestData.append('username', formData.username);
        requestData.append('password', formData.password);
        requestData.append('client_id', clientIdFromLogin);
        requestData.append('conn_name', formData.name);

        response = await fetch(`${API_BASE_URL_CONNECTOR}/validate/mysql`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: requestData,
        });
      } else if (selectedSource === 'postgresql') {
        const requestData = new URLSearchParams();
        requestData.append('host', formData.host);
        requestData.append('port', Number(formData.port));
        requestData.append('databaseName', formData.database);
        requestData.append('username', formData.username);
        requestData.append('password', formData.password);
        requestData.append('client_id', clientIdFromLogin);
        requestData.append('conn_name', formData.name);

        response = await fetch(`${API_BASE_URL_CONNECTOR}/validate/postgresql`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: requestData,
        });
      } else if (selectedSource === 'bigquery' || selectedSource === 'gcp-bucket') {
        // For GCP connections, we'll use the utility functions to store in GCS
        const form = new FormData();
        form.append('projectId', formData.projectId);
        form.append('datasetId', formData.datasetId);
        form.append('credentialFile', formData.credentialFile);
        form.append('client_id', clientIdFromLogin);
        form.append('conn_name', formData.name);
        form.append('connections_type', selectedSource);

        const endpoint = selectedSource === 'bigquery'
          ? '/validate/bigquery'
          : '/validate/gcp-bucket';

        response = await fetch(`${API_BASE_URL_CONNECTOR}${endpoint}`, {
          method: 'POST',
          body: form,
        });
      }

      const result = await response.json();
      console.log('API Response:', result); // Debug log
      console.log('Response status:', response.status); // Debug log
      
      if (response.ok && (result.status === 'success' || result.success)) {
        setTestStatus('success');
        setSubmissionMessage(result.message || 'Connection test successful! Credentials stored in GCS.');
        
        // Refresh connection history after successful test
        if (clientIdFromLogin) {
          fetch(`${API_BASE_URL_CONNECTOR}/connection-history/${clientIdFromLogin}`)
            .then(res => res.json())
            .then(data => setConnectionHistory(data.history || []))
            .catch(err => console.error('Error fetching connection history:', err));
        }
      } else {
        setTestStatus('failed');
        setSubmissionMessage(result.detail || result.message || 'Connection test failed. Please check credentials.');
      }
    } catch (error) {
      setTestStatus('failed');
      setSubmissionMessage('Connection test failed. ' + error.message);
    }
  };

  // Function to run discovery after successful connection
  const runDiscovery = async (clientId) => {
    setDiscoveryRunning(true);
    setDiscoveryProgress(0);
    let progress = 0;
    // Simulate progress bar
    const interval = setInterval(() => {
      progress += Math.floor(Math.random() * 10) + 5;
      setDiscoveryProgress(Math.min(progress, 95));
    }, 300);
    try {
      const response = await fetch(`${API_BASE_URL_DRIVER}/discover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_id: clientId })
      });
      clearInterval(interval);
      setDiscoveryProgress(100);
      setDiscoveryRunning(false);
      
      if (response.ok) {
        const result = await response.json();
        setShowToast(true);
        setSubmissionMessage(`Discovery completed successfully! Found ${result.results?.total_sources || 0} data sources.`);
        
        // Store discovery results for the discover page
        localStorage.setItem('discoveryResults', JSON.stringify(result));
        
        // Navigate to discover page after a brief delay
        setTimeout(() => {
          setShowToast(false);
          navigate('/discover');
        }, 2000);
      } else {
        const errorResult = await response.json();
        setShowToast(true);
        setSubmissionMessage(`Discovery failed: ${errorResult.detail || 'Unknown error'}`);
        setTimeout(() => setShowToast(false), 3000);
      }
    } catch (err) {
      clearInterval(interval);
      setDiscoveryRunning(false);
      setShowToast(true);
      setSubmissionMessage('Discovery failed: Network error');
      setTimeout(() => setShowToast(false), 3000);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validateStep(totalSteps)) { // Validate the final step before submission
      if (testStatus !== 'success') {
        setSubmissionMessage('Please test the connection and ensure it is successful before submitting.');
        return;
      }
      const newConnection = {
        id: Date.now(), // Simple unique ID
        name: formData.name,
        type: getTypeValue(), // Now accessible
        service: getServiceValue(), // Now accessible
        status: 'Connected', // Assuming successful submission means connected
        dateAdded: new Date().toLocaleString(),
        // Only store necessary data, exclude sensitive credentials for history display
        displayData: { ...formData }
      };
      // Remove sensitive data from displayData for security reasons
      delete newConnection.displayData.password;
      delete newConnection.displayData.credentialFile;

      setConnections(prev => [...prev, newConnection]);
      setSubmissionMessage('Data source connected successfully!');
      setFormData({}); // Clear form
      setSelectedSource(''); // Reset source selection
      setCurrentStep(1); // Go back to first step
      setTestStatus('idle'); // Reset test status
      if (fileInputRef.current) {
        fileInputRef.current.value = ''; // Clear file input
      }
      setShowToast(true);
      setTimeout(() => setShowToast(false), 2000);
      // Run discovery after connection is saved
      const user = JSON.parse(localStorage.getItem('user')) || {};
      const clientIdFromLogin = user.client_id || localStorage.getItem('client_id');
      if (clientIdFromLogin) {
        runDiscovery(clientIdFromLogin);
      }
    } else {
      setSubmissionMessage('Please correct the errors before submitting.');
    }
  };

  const handleEditConnection = (id) => {
    // In a real app, this would load the connection data into the form for editing
    console.log('Edit connection:', id);
    setSubmissionMessage('Edit functionality is a placeholder.');
  };

  const handleDeleteConnection = (id) => {
    setConnections(prev => prev.filter(conn => conn.id !== id));
    setSubmissionMessage('Connection deleted successfully.');
  };

  const handleDisableConnection = (id) => {
    setConnections(prev =>
      prev.map(conn =>
        conn.id === id ? { ...conn, status: conn.status === 'Disabled' ? 'Connected' : 'Disabled' } : conn
      )
    );
    setSubmissionMessage('Connection status updated.');
  };

  const handleImportConnections = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const importedData = JSON.parse(event.target.result);
          if (Array.isArray(importedData)) {
            const newConnections = importedData.map(item => ({
              id: Date.now() + Math.random(), // Assign new unique IDs
              name: item.name || 'Imported Connection',
              type: item.type || 'Unknown',
              service: item.service || 'Unknown',
              status: item.status || 'Connected',
              dateAdded: new Date().toLocaleString(),
              displayData: { ...item }
            }));
            setConnections(prev => [...prev, ...newConnections]);
            setSubmissionMessage(`Successfully imported ${newConnections.length} connections.`);
          } else {
            setSubmissionMessage('Import failed: Invalid file format. Please upload a JSON array.');
          }
        } catch (error) {
          setSubmissionMessage('Import failed: Could not parse file. Ensure it is valid JSON.');
          console.error('File import error:', error);
        }
      };
      reader.readAsText(file);
    }
  };

  // Get placeholder text based on selected source
  const getPlaceholders = () => {
    if (selectedSource === 'bigquery') {
      return {
        name: 'BigQuery Connection',
        projectId: 'your-gcp-project-id',
        datasetId: 'dataset-id without project prefix',
        description: 'Brief description of this BigQuery connection'
      };
    } else if (selectedSource === 'mysql') {
      return {
        name: 'MySQL Connection',
        host: 'localhost or IP address',
        port: '3306',
        databaseName: 'database_name',
        username: 'your_username',
        password: 'your_password'
      };
    } else if (selectedSource === 'gcp-bucket') {
      return {
        name: 'Bucket Connection',
        projectId: 'your-gcp-project-id',
        datasetId: 'your-bucket-name',
        description: 'Brief description of this GCP Bucket connection'
      };
    } else if (selectedSource === 'postgresql') {
      return {
        name: 'PostgreSQL Connection',
        host: 'localhost or IP address',
        port: '5432',
        database: 'database_name',
        username: 'your_username',
        password: 'your_password'
      };
    }
    return {};
  };

  const handleSourceChange = (e) => {
    const newSource = e.target.value;
    setSelectedSource(newSource);
    
    if (newSource) {
      // Clear form data and show placeholders instead of pre-filling
      setFormData({});
      setValidationErrors({});
      setSubmissionMessage('Template selected. Please fill in your connection details.');
      setCurrentStep(1); // Go to first step of the form
      setTestStatus('idle');
      if (fileInputRef.current) {
        fileInputRef.current.value = ''; // Clear file input
      }
    } else {
      // No source selected
      setFormData({}); // Reset form data when source changes
      setValidationErrors({});
      setSubmissionMessage('');
      setCurrentStep(1); // Reset to first step
      setTestStatus('idle'); // Reset test status
      if (fileInputRef.current) {
        fileInputRef.current.value = ''; // Clear file input
      }
    }
  };


  return (
    <div className="connect-page">
      <div className="connect-container">
        {/* Header Section */}
        <div className="connect-header">
          <div className="header-content">
            <div className="header-text">
              <h1 className="page-title">Connect Data Sources</h1>
              <p className="description-text">
                Select a data source type to configure your connection and start analyzing your data.
              </p>
            </div>
            <div className="header-actions">
              <button 
                className="discover-button"
                onClick={() => navigate('/discover')}
                title="Explore and analyze your existing data sources"
              >
                Data Sources Already Connected
                 Discover Now
              </button>
            </div>
          </div>
        </div>

        {/* Connect New Container */}
        <div className="connect-new-container">
          <h2 className="container-title">Connect New</h2>
          <div className="source-selection">
            <label className="form-label">Choose Data Source Type:</label>
            <select
              id="dataSourceType"
              value={selectedSource}
              onChange={handleSourceChange}
              className="form-select"
            >
              <option value="">Select a type</option>
              <option value="bigquery">BigQuery</option>
              <option value="gcp-bucket">GCP Bucket</option>
              <option value="mysql">MySQL</option>
              <option value="postgresql">PostgreSQL</option>
            </select>
          </div>

      {selectedSource && (
        <div className="form-container">
          <div className="step-indicator">
            <span className={`step ${currentStep === 1 ? 'active' : currentStep > 1 ? 'completed' : ''}`}>1</span>
            <span className={`step-line ${currentStep > 1 ? 'completed' : ''}`}></span>
            <span className={`step ${currentStep === 2 ? 'active' : currentStep > 2 ? 'completed' : ''}`}>2</span>
          </div>
          <DynamicForm
            selectedSource={selectedSource}
            onInputChange={handleInputChange}
            onFileChange={handleFileChange}
            formData={formData}
            validationErrors={validationErrors}
            onFormSubmit={handleSubmit}
            fileInputRef={fileInputRef}
            currentStep={currentStep}
            onNextStep={handleNextStep}
            onPreviousStep={handlePreviousStep}
            isLastStep={isLastStep}
            onTestConnection={handleTestConnection}
            testStatus={testStatus}
            getTypeValue={getTypeValue} 
            getServiceValue={getServiceValue} 
            submitEnabled={testStatus === 'success'}
            validateStep={validateStep}
            totalSteps={totalSteps}
            setSubmissionMessage={setSubmissionMessage}
            setConnections={setConnections}
            setFormData={setFormData}
            setSelectedSource={setSelectedSource}
            setCurrentStep={setCurrentStep}
            setTestStatus={setTestStatus}
            setShowToast={setShowToast}
            runDiscovery={runDiscovery}
            getPlaceholders={getPlaceholders}
          />
        </div>
      )}

      {submissionMessage && (
        <div className={`submission-message ${
          submissionMessage.includes('Error') || submissionMessage.includes('failed') ? 'error' : 
          submissionMessage.includes('Template selected') ? 'template' : 'success'
        }`}>
          {submissionMessage}
        </div>
      )}
        </div>

        {/* Discovery Progress */}
        {discoveryRunning && (
          <div className="pipeline-progress">
            <div className="pipeline-header">Running Data Discovery...</div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${discoveryProgress}%` }}></div>
            </div>
            <div className="progress-text">{discoveryProgress}%</div>
          </div>
        )}

        {/* Connection Attempt History Container */}
        <div className="connection-history-container">
          <h2 className="container-title">Connection Attempt History</h2>
          {connectionHistory.length > 0 ? (
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Attempt ID</th>
                    <th>Connection Name</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Last Used</th>
                    <th>Created At</th>
                  </tr>
                </thead>
                <tbody>
                  {connectionHistory.map(hist => (
                    <tr key={hist.cli_conn_hist_id}>
                      <td>{hist.cli_conn_hist_id}</td>
                      <td>{hist.conn_name}</td>
                      <td>{hist.connections_type}</td>
                      <td>
                        <span className={`status-badge ${hist.connection_status === 'success' ? 'success' : 'failed'}`}>
                          {hist.connection_status}
                        </span>
                      </td>
                      <td>{hist.last_used ? new Date(hist.last_used).toLocaleString() : '-'}</td>
                      <td>{hist.created_at ? new Date(hist.created_at).toLocaleString() : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="empty-state">No connection attempts yet.</p>
          )}
        </div>

        {/* Connection History Container */}
        {/* <div className="connection-management-container">
          <h2 className="container-title">Connection History</h2>
          {connections.length > 0 ? (
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Service</th>
                    <th>Status</th>
                    <th>Date Added</th>
                  </tr>
                </thead>
                <tbody>
                  {connections.map(conn => (
                    <tr key={conn.id} className={conn.status === 'Disabled' ? 'disabled-row' : ''}>
                      <td>{conn.name}</td>
                      <td>{conn.type}</td>
                      <td>{conn.service}</td>
                      <td>
                        <span className={`status-badge ${conn.status.toLowerCase()}`}>
                          {conn.status}
                        </span>
                      </td>
                      <td>{conn.dateAdded}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="empty-state">No connections added yet.</p>
          )}
        </div> */}

      {/* Toast Notifications */}
      {showToast && (
        <div className="toast-overlay">
          <div className={`toast ${submissionMessage.toLowerCase().includes('success') ? 'toast-success' : 
            submissionMessage.toLowerCase().includes('error') || submissionMessage.toLowerCase().includes('fail') ? 'toast-error' : 'toast-info'}`}>
            {submissionMessage || 'Data source connected successfully!'}
          </div>
        </div>
      )}

      </div>
    </div>
  );
}

export default ConnectPage;