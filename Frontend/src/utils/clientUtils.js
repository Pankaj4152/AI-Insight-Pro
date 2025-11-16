// Utility functions for client management

/**
 * Get the current client ID based on user role
 * For compliance officers: returns selected client ID from dropdown
 * For regular users: returns their own client ID
 */
export const getCurrentClientId = () => {
  const userData = JSON.parse(localStorage.getItem('user') || '{}');
  const isComplianceOfficer = userData.role === 'compliance-officer';
  
  if (isComplianceOfficer) {
    // For compliance officers, use selected client ID or first available
    const selectedClientId = localStorage.getItem('selected_client_id');
    if (selectedClientId) {
      return selectedClientId;
    }
    
    // Fallback to first client in the list
    const clientIdList = JSON.parse(localStorage.getItem('client_id_list') || '{}');
    const firstClientId = Object.values(clientIdList)[0];
    if (firstClientId) {
      localStorage.setItem('selected_client_id', firstClientId);
      return firstClientId;
    }
    
    return userData.client_id || '';
  }
  
  // For regular users, return their own client ID
  return userData.client_id || localStorage.getItem('client_id') || '';
};

/**
 * Get the current user data
 */
export const getCurrentUser = () => {
  return JSON.parse(localStorage.getItem('user') || '{}');
};

/**
 * Check if current user is a compliance officer
 */
export const isComplianceOfficer = () => {
  const userData = getCurrentUser();
  return userData.role === 'compliance-officer';
};

/**
 * Get the client ID list for compliance officers
 */
export const getClientIdList = () => {
  return JSON.parse(localStorage.getItem('client_id_list') || '{}');
};

/**
 * Set the selected client ID for compliance officers
 */
export const setSelectedClientId = (clientId) => {
  localStorage.setItem('selected_client_id', clientId);
};

// Cache for performance optimization
let _cachedRiskClientId = null;
let _lastCacheTime = 0;
const CACHE_DURATION = 5000; // 5 seconds cache

/**
 * Get client ID for risk assessment and dashboard data (OPTIMIZED with caching)
 * For compliance officers: returns selected client ID from dropdown
 * For regular users: returns their own client ID
 */
export const getRiskAssessmentClientId = () => {
  const now = Date.now();

  // Return cached value if still valid
  if (_cachedRiskClientId && (now - _lastCacheTime) < CACHE_DURATION) {
    return _cachedRiskClientId;
  }

  // Compute new value
  const userData = JSON.parse(localStorage.getItem('user') || '{}');
  const isComplianceOfficer = userData.role === 'compliance-officer';

  let clientId;

  if (isComplianceOfficer) {
    // For compliance officers, always use selected client ID from dropdown
    const selectedClientId = localStorage.getItem('selected_client_id');
    if (selectedClientId) {
      clientId = selectedClientId;
    } else {
      // Fallback to first client in the list
      const clientIdList = JSON.parse(localStorage.getItem('client_id_list') || '{}');
      const firstClientId = Object.values(clientIdList)[0];
      if (firstClientId) {
        localStorage.setItem('selected_client_id', firstClientId);
        clientId = firstClientId;
      } else {
        clientId = null; // No client selected
      }
    }
  } else {
    // For regular users, return their own client ID
    clientId = userData.client_id || localStorage.getItem('client_id') || '';
  }

  // Cache the result
  _cachedRiskClientId = clientId;
  _lastCacheTime = now;

  return clientId;
};

/**
 * Clear the risk assessment client ID cache (call when client selection changes)
 */
export const clearRiskAssessmentClientIdCache = () => {
  _cachedRiskClientId = null;
  _lastCacheTime = 0;
};
