// Utility functions for the risk assessment dashboard
import { getCurrentClientId, getRiskAssessmentClientId } from './clientUtils';

// Format numbers with commas
export const formatNumber = (num) => {
  if (num === null || num === undefined) return 'N/A';
  if (typeof num !== 'number') return num;
  return num.toLocaleString();
};

// Format percentage
export const formatPercentage = (num, decimals = 1) => {
  if (num === null || num === undefined) return 'N/A';
  if (typeof num !== 'number') return num;
  return `${num.toFixed(decimals)}%`;
};

// Format date
export const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    return 'Invalid Date';
  }
};

// Get risk level color
export const getRiskColor = (level) => {
  switch (level?.toLowerCase()) {
    case 'critical': return '#DC2626';
    case 'high': return '#EF4444';
    case 'medium': return '#F59E0B';
    case 'low': return '#10B981';
    default: return '#6B7280';
  }
};

// Get confidence color
export const getConfidenceColor = (score) => {
  if (score >= 80) return '#10B981';
  if (score >= 60) return '#F59E0B';
  return '#EF4444';
};

// Export data to CSV
export const exportToCSV = (data, filename = 'risk_findings') => {
  if (!data || data.length === 0) {
    alert('No data to export');
    return;
  }

  // Get all unique keys from the data
  const headers = [...new Set(data.flatMap(Object.keys))];
  
  // Create CSV content
  const csvContent = [
    headers.join(','), // Header row
    ...data.map(row => 
      headers.map(header => {
        const value = row[header];
        // Escape commas and quotes in CSV
        if (value === null || value === undefined) return '';
        const stringValue = String(value);
        if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
          return `"${stringValue.replace(/"/g, '""')}"`;
        }
        return stringValue;
      }).join(',')
    )
  ].join('\n');

  // Create and download file
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.setAttribute('href', url);
  link.setAttribute('download', `${filename}_${new Date().toISOString().split('T')[0]}.csv`);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// Debounce function for search
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// Handle API errors
export const handleApiError = (error, showNotification) => {
  console.error('API Error:', error);
  
  let message = 'An unexpected error occurred';
  
  if (error.message.includes('Failed to fetch')) {
    message = 'Network error - please check your connection';
  } else if (error.message.includes('401')) {
    message = 'Authentication failed - please log in again';
  } else if (error.message.includes('403')) {
    message = 'Access denied - insufficient permissions';
  } else if (error.message.includes('404')) {
    message = 'Requested resource not found';
  } else if (error.message.includes('500')) {
    message = 'Server error - please try again later';
  } else if (error.message) {
    message = error.message;
  }
  
  if (showNotification) {
    showNotification(message, 'error');
  }
  
  return message;
};

// Calculate trend percentage
export const calculateTrend = (current, previous) => {
  if (!previous || previous === 0) return 0;
  return ((current - previous) / previous) * 100;
};

// Generate random color for charts
export const generateChartColors = (count) => {
  const colors = [
    '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
    '#06B6D4', '#EC4899', '#6B7280', '#84CC16', '#F97316'
  ];
  
  const result = [];
  for (let i = 0; i < count; i++) {
    result.push(colors[i % colors.length]);
  }
  
  return result;
};

// Validate and clean data
export const cleanChartData = (data, type = 'number') => {
  if (!Array.isArray(data)) return [];
  
  return data.map(item => {
    if (type === 'number') {
      const num = Number(item);
      return isNaN(num) ? 0 : num;
    }
    return item || 'Unknown';
  });
};

// Get current user safely
export const getCurrentUser = () => {
  try {
    const user = JSON.parse(localStorage.getItem('user'));
    if (user && user.client_id) return user;
  } catch (error) {
    console.error('Error parsing user data:', error);
  }

  const client_id = getCurrentClientId();
  if (!client_id) {
    throw new Error('No client_id found - please log in again');
  }

  return {
    client_id: client_id,
    client_name: localStorage.getItem('client_name') || 'Unknown',
    email: localStorage.getItem('client_email') || 'unknown@example.com'
  };
};

// Cache for performance
let _cachedRiskUser = null;
let _lastUserCacheTime = 0;
const USER_CACHE_DURATION = 3000; // 3 seconds cache

// Get current user for risk assessment (uses selected client for compliance officers)
export const getRiskAssessmentUser = () => {
  const now = Date.now();

  // Return cached value if still valid
  if (_cachedRiskUser && (now - _lastUserCacheTime) < USER_CACHE_DURATION) {
    return _cachedRiskUser;
  }

  let user;

  try {
    const userData = JSON.parse(localStorage.getItem('user'));
    if (userData && userData.role === 'compliance-officer') {
      // For compliance officers, return user info but with selected client_id
      const selectedClientId = getRiskAssessmentClientId();
      if (!selectedClientId) {
        throw new Error('No client selected - please select a client from the dropdown');
      }
      user = {
        ...userData,
        client_id: selectedClientId,
        client_name: localStorage.getItem('client_name') || 'Unknown',
        email: localStorage.getItem('client_email') || 'unknown@example.com'
      };
    } else if (userData && userData.client_id) {
      user = userData;
    } else {
      // Fallback for regular users
      const client_id = getCurrentClientId();
      if (!client_id) {
        throw new Error('No client_id found - please log in again');
      }
      user = {
        client_id: client_id,
        client_name: localStorage.getItem('client_name') || 'Unknown',
        email: localStorage.getItem('client_email') || 'unknown@example.com'
      };
    }
  } catch (error) {
    console.error('Error getting risk assessment user:', error);
    throw error;
  }

  // Cache the result
  _cachedRiskUser = user;
  _lastUserCacheTime = now;

  return user;
};

// Local storage utilities
export const setStorageItem = (key, value) => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error('Error saving to localStorage:', error);
  }
};

export const getStorageItem = (key, defaultValue = null) => {
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch (error) {
    console.error('Error reading from localStorage:', error);
    return defaultValue;
  }
};

// Chart.js common options
export const getDefaultChartOptions = (title) => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    title: {
      display: !!title,
      text: title,
      font: {
        size: 16,
        weight: 'bold'
      }
    },
    legend: {
      position: 'bottom',
      labels: {
        font: { size: 12 },
        padding: 15,
        usePointStyle: true
      }
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleFont: { size: 12 },
      bodyFont: { size: 12 },
      padding: 10,
      cornerRadius: 6
    }
  }
});

export const getPieChartOptions = (title) => ({
  ...getDefaultChartOptions(title),
  cutout: '50%'
});

export const getLineChartOptions = (title) => ({
  ...getDefaultChartOptions(title),
  scales: {
    x: {
      grid: {
        display: false
      },
      ticks: {
        font: { size: 11 }
      }
    },
    y: {
      beginAtZero: true,
      grid: {
        color: 'rgba(0, 0, 0, 0.1)'
      },
      ticks: {
        font: { size: 11 }
      }
    }
  },
  elements: {
    line: {
      tension: 0.4
    },
    point: {
      radius: 3,
      hoverRadius: 6
    }
  }
});

export const getBarChartOptions = (title) => ({
  ...getDefaultChartOptions(title),
  scales: {
    x: {
      grid: {
        display: false
      },
      ticks: {
        font: { size: 11 }
      }
    },
    y: {
      beginAtZero: true,
      grid: {
        color: 'rgba(0, 0, 0, 0.1)'
      },
      ticks: {
        font: { size: 11 }
      }
    }
  }
});
