// src/utils/apiIntegration.js
// Comprehensive API integration utilities for full backend integration

import {
  API_BASE_URL,
  API_BASE_URL_CONNECTOR,
  API_BASE_URL_DRIVER,
  API_BASE_URL_CHATBOT,
  API_BASE_URL_CLIENT_CHATBOT,
  API_LOGIN_URL
} from '../apiConfig';
import { getCurrentClientId, getRiskAssessmentClientId } from './clientUtils';

// Helper function to get client ID from various storage locations
export const getClientId = () => {
  return getCurrentClientId() ||
         sessionStorage.getItem('client_id') ||
         localStorage.getItem('signup_client_id') ||
         'demo-client';
};

// Helper function to get client ID for risk assessment (uses selected client for compliance officers)
export const getRiskClientId = () => {
  // Quick check if user is compliance officer
  const userData = JSON.parse(localStorage.getItem('user') || '{}');
  if (userData.role === 'compliance-officer') {
    return getRiskAssessmentClientId() || 'demo-client';
  }

  // For regular users, use the faster path
  return getCurrentClientId() ||
         sessionStorage.getItem('client_id') ||
         localStorage.getItem('signup_client_id') ||
         'demo-client';
};

// Generic API call wrapper with error handling
export const apiCall = async (url, options = {}) => {
  const clientId = getClientId();
  
  const defaultHeaders = {
    'Content-Type': 'application/json',
    'X-Client-ID': clientId,
  };

  const config = {
    headers: { ...defaultHeaders, ...options.headers },
    ...options
  };

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    return { success: true, data };
  } catch (error) {
    console.error('API call failed:', error);
    return { success: false, error: error.message };
  }
};

// SDE Management APIs
export const sdeAPI = {
  // Get available SDEs by industry
  getSDEsByIndustry: async (industry) => {
    return apiCall(`${API_BASE_URL_CONNECTOR}/get-sde?selected_industry=${encodeURIComponent(industry)}`);
  },

  // Get industry classifications
  getIndustryClassifications: async () => {
    return apiCall(`${API_BASE_URL_CONNECTOR}/industry-classifications`);
  },

  // Add new SDE
  addSDE: async (sdeData) => {
    return apiCall(`${API_BASE_URL_CONNECTOR}/add-sde`, {
      method: 'POST',
      body: JSON.stringify(sdeData)
    });
  },

  // Get available SDE patterns
  getAvailableSDEs: async () => {
    return apiCall(`${API_BASE_URL_DRIVER}/available-sdes`);
  },

  // Get client SDE selections
  getClientSDEs: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL_DRIVER}/client-sdes/${id}`);
  },

  // Update client SDE selections
  updateClientSDEs: async (patternNames, clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL_DRIVER}/client-sdes`, {
      method: 'POST',
      body: JSON.stringify({
        client_id: id,
        pattern_names: patternNames
      })
    });
  }
};

// Data Scanning APIs
export const scanAPI = {
  // Scan latest database
  scanLatest: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL_DRIVER}/scan-latest`, {
      method: 'POST',
      body: JSON.stringify({ client_id: id })
    });
  },

  // Scan all databases
  scanAll: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL_DRIVER}/scan-all`, {
      method: 'POST',
      body: JSON.stringify({ client_id: id })
    });
  },

  // Scan specific database
  scanSpecific: async (storeName, tables = null, clientId = null) => {
    const id = clientId || getClientId();
    const body = { client_id: id, store_name: storeName };
    if (tables) body.tables = tables;
    
    return apiCall(`${API_BASE_URL_DRIVER}/scan-specific`, {
      method: 'POST',
      body: JSON.stringify(body)
    });
  },

  // Run complete pipeline
  runPipeline: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL_DRIVER}/run-pipeline`, {
      method: 'POST',
      body: JSON.stringify({ client_id: id })
    });
  },

  // Data discovery
  discover: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL_DRIVER}/discover`, {
      method: 'POST',
      body: JSON.stringify({ client_id: id })
    });
  },

  // List client databases
  listDatabases: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL_DRIVER}/list-databases/${id}`);
  },

  // Save file selection for scanning
  saveSelection: async (selectedFiles, clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL_DRIVER}/save-selection`, {
      method: 'POST',
      body: JSON.stringify({
        client_id: id,
        selected_files: selectedFiles
      })
    });
  }
};

// Risk Assessment APIs
export const riskAPI = {
  // Core risk assessment
  performRiskAssessment: async (riskLevel = null, sensitivity = null, dataSource = null, clientId = null) => {
    const id = clientId || getRiskClientId();
    const body = { client_id: id };
    if (riskLevel) body.risk_level = riskLevel;
    if (sensitivity) body.sensitivity = sensitivity;
    if (dataSource) body.data_source = dataSource;

    return apiCall(`${API_BASE_URL}/risk/risk-assessment`, {
      method: 'POST',
      body: JSON.stringify(body)
    });
  },

  // Get risk assessments history
  getRiskAssessments: async (limit = 10, clientId = null) => {
    const id = clientId || getRiskClientId();
    return apiCall(`${API_BASE_URL}/risk/risk-assessments/${id}?limit=${limit}`);
  },

  // Get all metrics in one call
  getAllMetrics: async (clientId = null) => {
    const id = clientId || getRiskClientId();
    return apiCall(`${API_BASE_URL}/risk/all-metrics/${id}`);
  },

  // Individual metrics
  getTotalDataSources: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/total-data-sources/${id}`);
  },

  getTotalSDEs: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/total-sdes/${id}`);
  },

  getScannedSDEs: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/scanned-sdes/${id}`);
  },

  getHighRiskSDEs: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/high-risk-sdes/${id}`);
  },

  getHighRiskRecords: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/high-risk-records/${id}`);
  },

  getTotalSensitiveRecords: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/total-sensitive-records/${id}`);
  },

  getTotalScans: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/total-scans/${id}`);
  },

  getRiskScore: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/risk-score/${id}`);
  },

  getConfidenceScore: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/confidence-score/${id}`);
  },

  getLastScanTime: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/last-scan-time/${id}`);
  },

  getNextScheduledScan: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/next-scheduled-scan/${id}`);
  },

  getLLMSummary: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/llm-summary/${id}`);
  },

  // Dashboard APIs
  getComprehensiveDashboard: async (clientId = null) => {
    const id = clientId || getRiskClientId();
    return apiCall(`${API_BASE_URL}/risk/comprehensive-dashboard/${id}`);
  },

  getComprehensiveRiskAssessment: async (clientId = null) => {
    const id = clientId || getRiskClientId();
    return apiCall(`${API_BASE_URL}/risk/comprehensive-risk-assessment/${id}`);
  },

  getDataSourceTypes: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/data-source-types/${id}`);
  },

  getRiskLevelDistribution: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/risk-level-distribution/${id}`);
  },

  getSensitivityCategories: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/sensitivity-categories/${id}`);
  },

  getScanActivityTimeline: async (days = 30, clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/scan-activity-timeline/${id}?days=${days}`);
  },

  getTopRiskLocations: async (limit = 10, clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/top-risk-locations/${id}?limit=${limit}`);
  },

  // Data Analysis APIs
  getSDECategoryDistribution: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/sde-category-distribution/${id}`);
  },

  getDetectionMethodStats: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/detection-method-stats/${id}`);
  },

  getConfidenceScoreDistribution: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/confidence-score-distribution/${id}`);
  },

  getFieldTypeAnalysis: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/field-type-analysis/${id}`);
  },

  getPrivacyViolationTypes: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/privacy-violation-types/${id}`);
  },

  getRiskMatrixData: async (clientId = null) => {
    const id = clientId || getRiskClientId();
    return apiCall(`${API_BASE_URL}/risk/risk-matrix-data/${id}`);
  },

  getTrendAnalysis: async (days = 30, clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/trend-analysis/${id}?days=${days}`);
  },

  getSensitivityBySource: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/sensitivity-by-source/${id}`);
  }
};

// Report APIs
export const reportAPI = {
  generateReport: async (format = 'pdf', name = '', email = '', company = '', clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/report`, {
      method: 'POST',
      body: JSON.stringify({
        client_id: id,
        format,
        name,
        email,
        company
      })
    });
  },

  previewReport: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/preview-report?client_id=${id}`);
  },

  downloadReport: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/download-report?client_id=${id}`);
  }
};

// Health check
export const healthAPI = {
  checkHealth: async () => {
    return apiCall(`${API_BASE_URL_DRIVER}/health`);
  }
};

// Combined API for easy access
export const api = {
  sde: sdeAPI,
  scan: scanAPI,
  risk: riskAPI,
  report: reportAPI,
  health: healthAPI,
  getClientId,
  apiCall
};

export default api;
