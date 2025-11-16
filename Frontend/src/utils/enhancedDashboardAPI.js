// src/utils/enhancedDashboardAPI.js
// Enhanced API utilities for comprehensive dashboard graphs - Now using apiIntegration

import { api } from './apiIntegration';

// Re-export the comprehensive API functionality
export const dashboardAPI = api.risk;
export const getClientId = api.getClientId;
export const apiCall = api.apiCall;

// Re-export specific dashboard functions for backward compatibility
export const fetchComprehensiveDashboard = () => api.risk.getComprehensiveDashboard();
export const fetchComprehensiveRiskAssessment = () => api.risk.getComprehensiveRiskAssessment();
export const fetchDataStoreTypesDistribution = () => api.risk.getDataSourceTypes();
export const fetchRiskScoreOverTime = (days = 30) => api.risk.getTrendAnalysis(days);
export const fetchScanHistory = (days = 30) => api.risk.getScanActivityTimeline(days);
export const fetchRiskLevelDistribution = () => api.risk.getRiskLevelDistribution();
export const fetchSensitivityCategories = () => api.risk.getSensitivityCategories();
export const fetchTopRiskLocations = (limit = 10) => api.risk.getTopRiskLocations(limit);
export const fetchSDECategoryDistribution = () => api.risk.getSDECategoryDistribution();
export const fetchDetectionMethodStats = () => api.risk.getDetectionMethodStats();
export const fetchConfidenceScoreDistribution = () => api.risk.getConfidenceScoreDistribution();
export const fetchFieldTypeAnalysis = () => api.risk.getFieldTypeAnalysis();
export const fetchPrivacyViolationTypes = () => api.risk.getPrivacyViolationTypes();
export const fetchRiskMatrixData = () => api.risk.getRiskMatrixData();
export const fetchSensitivityBySource = () => api.risk.getSensitivityBySource();

// Individual metrics
export const fetchTotalDataSources = () => api.risk.getTotalDataSources();
export const fetchTotalSDEs = () => api.risk.getTotalSDEs();
export const fetchScannedSDEs = () => api.risk.getScannedSDEs();
export const fetchHighRiskSDEs = () => api.risk.getHighRiskSDEs();
export const fetchHighRiskRecords = () => api.risk.getHighRiskRecords();
export const fetchTotalSensitiveRecords = () => api.risk.getTotalSensitiveRecords();
export const fetchTotalScans = () => api.risk.getTotalScans();
export const fetchOverallRiskScore = () => api.risk.getRiskScore();
export const fetchConfidenceScore = () => api.risk.getConfidenceScore();
export const fetchLastScanTime = () => api.risk.getLastScanTime();
export const fetchNextScheduledScan = () => api.risk.getNextScheduledScan();
export const fetchLLMSummary = () => api.risk.getLLMSummary();

// Legacy function names for backward compatibility
export const fetchComplianceStatus = fetchComprehensiveDashboard;
export const fetchTop5SDEsByFindings = fetchSDECategoryDistribution;
export const fetchNewFindingsPerScan = fetchScanHistory;
export const fetchComplianceSummary = fetchComprehensiveDashboard;
export const fetchHighRiskFindings = fetchHighRiskSDEs;
export const fetchAverageScanDuration = fetchLastScanTime;

// Batch data fetching using the new API
export const fetchAllDashboardData = async () => {
  try {
    const result = await api.risk.getComprehensiveDashboard();
    if (result.success) {
      return result.data;
    } else {
      throw new Error(result.error);
    }
  } catch (error) {
    console.error('Error fetching all dashboard data:', error);
    return {
      metrics: {},
      charts: {}
    };
  }
};

export const fetchAllRiskAnalysisData = async () => {
  try {
    const result = await api.risk.getComprehensiveRiskAssessment();
    if (result.success) {
      return result.data;
    } else {
      throw new Error(result.error);
    }
  } catch (error) {
    console.error('Error fetching all risk analysis data:', error);
    return {};
  }
};
