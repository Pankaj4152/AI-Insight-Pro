import React, { useState, useEffect } from 'react';
import { BadgeCheck, XCircle, AlertCircle, Loader, User, Zap, BarChart, FileText, CheckCircle, Code } from 'lucide-react';
import '../Css/Compliance.css';
import { API_BASE_URL_COMPLIANCE, API_LOGIN_URL } from '../apiConfig';
import { getCurrentClientId } from '../utils/clientUtils';

const Compliance = () => {
  const [clientId, setClientId] = useState('');
  const [username, setUsername] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Automatically fetch the client ID and username from localStorage/API on component load
  useEffect(() => {
    const storedClientId = getCurrentClientId();
    if (storedClientId) {
      setClientId(storedClientId);

      // Fetch username from profile API (same logic as ProfilePage)
      fetch(`${API_LOGIN_URL}/get-profile?client_id=${storedClientId}`)
        .then(res => res.json())
        .then(data => {
          if (data.username) {
            setUsername(data.username);
          }
        })
        .catch(err => {
          console.error('Error fetching username:', err);
          // Fallback to stored username if API fails
          const storedUsername = localStorage.getItem('profile_username');
          if (storedUsername) {
            setUsername(storedUsername);
          }
        });
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResponse(null);

    if (!clientId) {
      setError('Client ID not found. Please log in to proceed.');
      setLoading(false);
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL_COMPLIANCE}/calculate_compliance`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ client_id: clientId }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error || 'Something went wrong on the server.');
      } else {
        setResponse(data);
      }
    } catch (err) {
      setError('Failed to connect to the backend server. Please ensure it is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Highly Compliant':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'Partially Compliant':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'Low Compliance':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'Highly Compliant':
        return <BadgeCheck size={20} className="text-green-600" />;
      case 'Partially Compliant':
        return <AlertCircle size={20} className="text-yellow-600" />;
      case 'Low Compliance':
        return <XCircle size={20} className="text-red-600" />;
      default:
        return null;
    }
  };

  return (
    <div className="compliance-container p-6 md:p-10">
      <div className="page-header">
        <h1 className="page-title text-center">Compliance Score</h1>
        <p className="page-subtitle">
          Now your Industry's compliance score is just a click away!
        </p>
      </div>

      <div className="compliance-content-grid mt-12">
        {/* Input Card with Gradient */}
        <div className="compliance-input-card card-gradient">
          <div className="flex items-center mb-4">
            <Zap size={24} className="text-white mr-2" />
            <h2 className="text-xl font-semibold text-white">Get Compliance Status</h2>
          </div>
          <p className="text-sm text-gray-100 mb-6">
            Click the button below to fetch your compliance status using your logged-in user ID.
          </p>
          {username && (
            <div className="text-sm text-gray-200 mb-6">
              **Logged in as:** {username}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-6">
            <button
              type="submit"
              disabled={loading || !clientId}
              className={`compliance-btn ${loading || !clientId ? 'disabled' : ''}`}
            >
              {loading ? (
                <Loader className="animate-spin text-white" size={20} />
              ) : (
                'Generate Compliance'
              )}
            </button>
          </form>
        </div>

        {/* Results Card */}
        <div className="compliance-results-card">
          {error && (
            <div className="p-4 bg-red-50 rounded-lg shadow-sm">
              <div className="flex items-center space-x-2 text-red-700 font-medium">
                <XCircle size={20} />
                <span>Error: {error}</span>
              </div>
            </div>
          )}
          {!response && !error && (
            <div className="flex flex-col items-center justify-center h-full">
              <FileText size={64} className="text-gray-300" />
              <p className="mt-4 text-gray-500 text-center">Click the button to get your compliance status.</p>
            </div>
          )}
          {response && (
            <div className="compliance-report-content">
              <div className="report-header">
                <h2 className="report-title">
                  <FileText className="mr-2 text-indigo-600" size={28} />
                  Compliance Status
                </h2>
                <div className={`status-badge border ${getStatusColor(response.status)}`}>
                  {getStatusIcon(response.status)}
                  <span className="font-semibold">{response.status}</span>
                </div>
              </div>

              <div className="report-body">
                <div className="flex-grow space-y-4">
                  <div className="report-metric">
                    <span className="metric-label">Client ID:</span>
                    <span className="metric-value">{response.client_id}</span>
                  </div>
                  <div className="report-metric">
                    <span className="metric-label">Applicable Regulation:</span>
                    <span className="metric-value">{response.inferred_regulation}</span>
                  </div>
                </div>

                <div className="score-card">
                  <p className="score-label">Compliance Score</p>
                  <div className="score-value-container">
                    <span className="score-value">{response.score}%</span>
                  </div>
                </div>
              </div>

              <div className="report-section">
                <h3 className="section-title">
                  <Code className="mr-2 text-gray-500" size={20} />
                  Missing Required SDEs
                </h3>
                <ul className="list-disc pl-5 text-sm text-gray-600">
                  {response.missing_sdes.length > 0 ? (
                    response.missing_sdes.map((sde, index) => <li key={index}>{sde}</li>)
                  ) : (
                    <li className="flex items-center text-green-600">
                      <CheckCircle className="mr-2" size={16} /> All required SDEs are present.
                    </li>
                  )}
                </ul>
              </div>

              <div className="report-section mt-4">
                <h3 className="section-title">
                  <AlertCircle className="mr-2 text-yellow-500" size={20} />
                  Recommendation
                </h3>
                <p className="text-sm text-gray-600 mt-2">{response.recommendation}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Compliance;
