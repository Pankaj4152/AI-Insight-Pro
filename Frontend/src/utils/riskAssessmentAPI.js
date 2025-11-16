// src/utils/riskAssessmentAPI.js
// Comprehensive Risk Assessment API utilities using risk.py endpoints
// NO SQL QUERIES IN FRONTEND - All data comes from backend endpoints

import { API_BASE_URL } from '../apiConfig';
import { getClientId, apiCall } from './apiIntegration';

// ============================================================================
// CORE RISK ASSESSMENT ENDPOINTS
// ============================================================================

export const riskAssessmentAPI = {
  // Perform comprehensive risk assessment
  performRiskAssessment: async (riskLevel = null, sensitivity = null, dataSource = null, clientId = null) => {
    const id = clientId || getClientId();
    const body = { client_id: id };
    if (riskLevel) body.risk_level = riskLevel;
    if (sensitivity) body.sensitivity = sensitivity;
    if (dataSource) body.data_source = dataSource;

    return apiCall(`${API_BASE_URL}/risk/risk-assessment`, {
      method: 'POST',
      body: JSON.stringify(body)
    });
  },

  // Get risk assessment history
  getRiskAssessments: async (limit = 10, clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/risk-assessments/${id}?limit=${limit}`);
  },

  // Get comprehensive risk assessment
  getComprehensiveRiskAssessment: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/comprehensive-risk-assessment/${id}`);
  },

  // Get all metrics in one call
  getAllMetrics: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/all-metrics/${id}`);
  },

  // ============================================================================
  // INDIVIDUAL METRICS ENDPOINTS
  // ============================================================================

  // Data Sources
  getTotalDataSources: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/total-data-sources/${id}`);
  },

  getDataSources: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/data-sources/${id}`);
  },

  getDataSourceTypes: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/data-source-types/${id}`);
  },

  // SDEs and Findings
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

  // Scans and Activity
  getTotalScans: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/total-scans/${id}`);
  },

  getLastScanTime: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/last-scan-time/${id}`);
  },

  getNextScheduledScan: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/next-scheduled-scan/${id}`);
  },

  getScanActivity: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/scan-activity/${id}`);
  },

  getScanActivityTimeline: async (days = 30, clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/scan-activity-timeline/${id}?days=${days}`);
  },

  // Scores and Analysis
  getRiskScore: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/risk-score/${id}`);
  },

  getConfidenceScore: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/confidence-score/${id}`);
  },

  getLLMSummary: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/llm-summary/${id}`);
  },

  // ============================================================================
  // DASHBOARD AND CHART DATA ENDPOINTS
  // ============================================================================

  getComprehensiveDashboard: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/comprehensive-dashboard/${id}`);
  },

  getRiskLevelDistribution: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/risk-level-distribution/${id}`);
  },

  getSensitivityCategories: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/sensitivity-categories/${id}`);
  },

  getSensitivityBySource: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/sensitivity-by-source/${id}`);
  },

  getTopRiskLocations: async (limit = 10, clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/top-risk-locations/${id}?limit=${limit}`);
  },

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
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/risk-matrix-data/${id}`);
  },

  getTrendAnalysis: async (days = 30, clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/trend-analysis/${id}?days=${days}`);
  },

  // ============================================================================
  // FINDINGS AND FILTERING ENDPOINTS
  // ============================================================================

  getTopRiskFindings: async (limit = 10, sensitivity = null, riskLevel = null, clientId = null) => {
    const id = clientId || getClientId();
    let url = `${API_BASE_URL}/risk/top-findings/${id}?limit=${limit}`;
    if (sensitivity) url += `&sensitivity=${sensitivity}`;
    if (riskLevel) url += `&risk_level=${riskLevel}`;
    return apiCall(url);
  },

  getFilteredFindings: async (dataSource = null, riskLevel = null, sensitivity = null, clientId = null) => {
    const id = clientId || getClientId();
    let url = `${API_BASE_URL}/risk/filtered-findings/?client_id=${id}`;
    if (dataSource) url += `&data_source=${dataSource}`;
    if (riskLevel) url += `&risk_level=${riskLevel}`;
    if (sensitivity) url += `&sensitivity=${sensitivity}`;
    return apiCall(url);
  },

  getFindingsByDataStore: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/findings-by-data-store/${id}`);
  },

  getRegexPatternsMatched: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/regex-patterns-matched/${id}`);
  },

  getNewFindingsPerScan: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/new-findings-per-scan/${id}`);
  },

  getSDECount: async (patternName, dataSource, clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/sde-count/?pattern_name=${patternName}&data_source=${dataSource}`);
  },

  // ============================================================================
  // MODEL REGISTRY AND CONNECTION ENDPOINTS
  // ============================================================================

  getModelRegistryMetrics: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/model-registry-metrics/${id}`);
  },

  getConnectionStatus: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/connection-status/${id}`);
  },

  checkConnectionsExist: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/connections/exists/${id}`);
  },

  // ============================================================================
  // DATASET AND DEBUG ENDPOINTS
  // ============================================================================

  getDatasetNames: async (clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/dataset-names/${id}`);
  },

  debugRegexPatterns: async () => {
    return apiCall(`${API_BASE_URL}/risk/debug-regex-patterns`);
  },

  getDBStatus: async () => {
    return apiCall(`${API_BASE_URL}/risk/db-status`);
  },

  // ============================================================================
  // REPORT GENERATION ENDPOINTS
  // ============================================================================

  generateRiskReport: async (format = 'pdf', name = '', email = '', company = '', clientId = null) => {
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

  generateComplianceReport: async (format = 'pdf', name = '', email = '', company = '', clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/compliance-report`, {
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

  generateDatabaseReport: async (format = 'pdf', name = '', email = '', company = '', clientId = null) => {
    const id = clientId || getClientId();
    return apiCall(`${API_BASE_URL}/risk/database-report`, {
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

  // ============================================================================
  // UTILITY FUNCTIONS FOR FRONTEND COMPONENTS
  // ============================================================================

  // Load all dashboard data in parallel
  loadDashboardData: async (clientId = null) => {
    const id = clientId || getClientId();
    
    try {
      const [
        comprehensiveDashboard,
        comprehensiveRiskAssessment,
        allMetrics,
        topFindings,
        scanActivity,
        trendAnalysis
      ] = await Promise.allSettled([
        riskAssessmentAPI.getComprehensiveDashboard(id),
        riskAssessmentAPI.getComprehensiveRiskAssessment(id),
        riskAssessmentAPI.getAllMetrics(id),
        riskAssessmentAPI.getTopRiskFindings(10, null, null, id),
        riskAssessmentAPI.getScanActivity(id),
        riskAssessmentAPI.getTrendAnalysis(30, id)
      ]);

      return {
        dashboard: comprehensiveDashboard.status === 'fulfilled' ? comprehensiveDashboard.value : null,
        riskAssessment: comprehensiveRiskAssessment.status === 'fulfilled' ? comprehensiveRiskAssessment.value : null,
        metrics: allMetrics.status === 'fulfilled' ? allMetrics.value : null,
        topFindings: topFindings.status === 'fulfilled' ? topFindings.value : null,
        scanActivity: scanActivity.status === 'fulfilled' ? scanActivity.value : null,
        trendAnalysis: trendAnalysis.status === 'fulfilled' ? trendAnalysis.value : null
      };
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      throw error;
    }
  },

  // Load chart data for visualizations
  loadChartData: async (clientId = null) => {
    const id = clientId || getClientId();
    
    try {
      const [
        riskDistribution,
        sensitivityCategories,
        sensitivityBySource,
        sdeCategoryDistribution,
        detectionMethodStats,
        privacyViolationTypes,
        riskMatrixData
      ] = await Promise.allSettled([
        riskAssessmentAPI.getRiskLevelDistribution(id),
        riskAssessmentAPI.getSensitivityCategories(id),
        riskAssessmentAPI.getSensitivityBySource(id),
        riskAssessmentAPI.getSDECategoryDistribution(id),
        riskAssessmentAPI.getDetectionMethodStats(id),
        riskAssessmentAPI.getPrivacyViolationTypes(id),
        riskAssessmentAPI.getRiskMatrixData(id)
      ]);

      return {
        riskDistribution: riskDistribution.status === 'fulfilled' ? riskDistribution.value : null,
        sensitivityCategories: sensitivityCategories.status === 'fulfilled' ? sensitivityCategories.value : null,
        sensitivityBySource: sensitivityBySource.status === 'fulfilled' ? sensitivityBySource.value : null,
        sdeCategoryDistribution: sdeCategoryDistribution.status === 'fulfilled' ? sdeCategoryDistribution.value : null,
        detectionMethodStats: detectionMethodStats.status === 'fulfilled' ? detectionMethodStats.value : null,
        privacyViolationTypes: privacyViolationTypes.status === 'fulfilled' ? privacyViolationTypes.value : null,
        riskMatrixData: riskMatrixData.status === 'fulfilled' ? riskMatrixData.value : null
      };
    } catch (error) {
      console.error('Error loading chart data:', error);
      throw error;
    }
  },

  // Load metrics for dashboard cards
  loadMetrics: async (clientId = null) => {
    const id = clientId || getClientId();
    
    try {
      const [
        totalDataSources,
        totalSDEs,
        scannedSDEs,
        highRiskSDEs,
        highRiskRecords,
        totalSensitiveRecords,
        totalScans,
        riskScore,
        confidenceScore,
        lastScanTime
      ] = await Promise.allSettled([
        riskAssessmentAPI.getTotalDataSources(id),
        riskAssessmentAPI.getTotalSDEs(id),
        riskAssessmentAPI.getScannedSDEs(id),
        riskAssessmentAPI.getHighRiskSDEs(id),
        riskAssessmentAPI.getHighRiskRecords(id),
        riskAssessmentAPI.getTotalSensitiveRecords(id),
        riskAssessmentAPI.getTotalScans(id),
        riskAssessmentAPI.getRiskScore(id),
        riskAssessmentAPI.getConfidenceScore(id),
        riskAssessmentAPI.getLastScanTime(id)
      ]);

      return {
        totalDataSources: totalDataSources.status === 'fulfilled' ? totalDataSources.value : null,
        totalSDEs: totalSDEs.status === 'fulfilled' ? totalSDEs.value : null,
        scannedSDEs: scannedSDEs.status === 'fulfilled' ? scannedSDEs.value : null,
        highRiskSDEs: highRiskSDEs.status === 'fulfilled' ? highRiskSDEs.value : null,
        highRiskRecords: highRiskRecords.status === 'fulfilled' ? highRiskRecords.value : null,
        totalSensitiveRecords: totalSensitiveRecords.status === 'fulfilled' ? totalSensitiveRecords.value : null,
        totalScans: totalScans.status === 'fulfilled' ? totalScans.value : null,
        riskScore: riskScore.status === 'fulfilled' ? riskScore.value : null,
        confidenceScore: confidenceScore.status === 'fulfilled' ? confidenceScore.value : null,
        lastScanTime: lastScanTime.status === 'fulfilled' ? lastScanTime.value : null
      };
    } catch (error) {
      console.error('Error loading metrics:', error);
      throw error;
    }
  }
};

export default riskAssessmentAPI;
