# Frontend API Usage Guide
## Using risk.py Endpoints Instead of SQL Queries

This guide shows how to properly use the `risk.py` backend endpoints in the frontend instead of writing SQL queries directly in the frontend code.

## 🚫 What NOT to do (SQL Queries in Frontend)

```javascript
// ❌ WRONG - Don't write SQL queries in frontend
const fetchData = async () => {
  const response = await fetch('/api/query', {
    method: 'POST',
    body: JSON.stringify({
      query: "SELECT COUNT(*) FROM scan_findings WHERE client_id = '123'"
    })
  });
};
```

## ✅ What TO do (Use risk.py Endpoints)

### 1. Import the Risk Assessment API

```javascript
// Import the comprehensive risk assessment API
import riskAssessmentAPI from '../utils/riskAssessmentAPI';
```

### 2. Use Individual Endpoints

```javascript
// ✅ CORRECT - Use specific endpoints for each data need
const loadDashboardData = async (clientId) => {
  try {
    // Get total data sources
    const dataSources = await riskAssessmentAPI.getTotalDataSources(clientId);
    
    // Get total SDEs
    const totalSDEs = await riskAssessmentAPI.getTotalSDEs(clientId);
    
    // Get high risk findings
    const highRiskFindings = await riskAssessmentAPI.getHighRiskSDEs(clientId);
    
    // Get risk score
    const riskScore = await riskAssessmentAPI.getRiskScore(clientId);
    
    return {
      dataSources: dataSources.data?.total_data_sources || 0,
      totalSDEs: totalSDEs.data?.total_sdes || 0,
      highRiskFindings: highRiskFindings.data?.high_risk_sdes || 0,
      riskScore: riskScore.data?.risk_score || 0
    };
  } catch (error) {
    console.error('Error loading dashboard data:', error);
    return { error: 'Failed to load data' };
  }
};
```

### 3. Use Comprehensive Endpoints

```javascript
// ✅ CORRECT - Use comprehensive endpoints for multiple metrics
const loadAllMetrics = async (clientId) => {
  try {
    // Get all metrics in one call
    const allMetrics = await riskAssessmentAPI.getAllMetrics(clientId);
    
    // Get comprehensive dashboard data
    const dashboard = await riskAssessmentAPI.getComprehensiveDashboard(clientId);
    
    // Get comprehensive risk assessment
    const riskAssessment = await riskAssessmentAPI.getComprehensiveRiskAssessment(clientId);
    
    return {
      metrics: allMetrics.data,
      dashboard: dashboard.data,
      riskAssessment: riskAssessment.data
    };
  } catch (error) {
    console.error('Error loading comprehensive data:', error);
    return { error: 'Failed to load comprehensive data' };
  }
};
```

### 4. Use Chart Data Endpoints

```javascript
// ✅ CORRECT - Use specific endpoints for chart data
const loadChartData = async (clientId) => {
  try {
    const [
      riskDistribution,
      sensitivityCategories,
      trendAnalysis,
      riskMatrix
    ] = await Promise.all([
      riskAssessmentAPI.getRiskLevelDistribution(clientId),
      riskAssessmentAPI.getSensitivityCategories(clientId),
      riskAssessmentAPI.getTrendAnalysis(30, clientId),
      riskAssessmentAPI.getRiskMatrixData(clientId)
    ]);
    
    return {
      riskDistribution: riskDistribution.data,
      sensitivityCategories: sensitivityCategories.data,
      trendAnalysis: trendAnalysis.data,
      riskMatrix: riskMatrix.data
    };
  } catch (error) {
    console.error('Error loading chart data:', error);
    return { error: 'Failed to load chart data' };
  }
};
```

### 5. Use Utility Functions

```javascript
// ✅ CORRECT - Use the built-in utility functions
const loadDashboardData = async (clientId) => {
  try {
    // Load all dashboard data in parallel
    const dashboardData = await riskAssessmentAPI.loadDashboardData(clientId);
    
    // Load chart data
    const chartData = await riskAssessmentAPI.loadChartData(clientId);
    
    // Load metrics
    const metrics = await riskAssessmentAPI.loadMetrics(clientId);
    
    return {
      ...dashboardData,
      ...chartData,
      ...metrics
    };
  } catch (error) {
    console.error('Error loading data:', error);
    return { error: 'Failed to load data' };
  }
};
```

## 📊 Available Endpoints

### Core Risk Assessment
- `performRiskAssessment()` - Perform risk assessment
- `getRiskAssessments()` - Get assessment history
- `getComprehensiveRiskAssessment()` - Get comprehensive assessment
- `getAllMetrics()` - Get all metrics

### Individual Metrics
- `getTotalDataSources()` - Total data sources
- `getTotalSDEs()` - Total SDEs
- `getScannedSDEs()` - Scanned SDEs
- `getHighRiskSDEs()` - High risk SDEs
- `getHighRiskRecords()` - High risk records
- `getTotalSensitiveRecords()` - Total sensitive records
- `getTotalScans()` - Total scans
- `getRiskScore()` - Risk score
- `getConfidenceScore()` - Confidence score
- `getLastScanTime()` - Last scan time

### Dashboard and Charts
- `getComprehensiveDashboard()` - Complete dashboard data
- `getRiskLevelDistribution()` - Risk level distribution
- `getSensitivityCategories()` - Sensitivity categories
- `getSensitivityBySource()` - Sensitivity by source
- `getTopRiskLocations()` - Top risk locations
- `getSDECategoryDistribution()` - SDE category distribution
- `getDetectionMethodStats()` - Detection method stats
- `getPrivacyViolationTypes()` - Privacy violation types
- `getRiskMatrixData()` - Risk matrix data
- `getTrendAnalysis()` - Trend analysis

### Findings and Filtering
- `getTopRiskFindings()` - Top risk findings
- `getFilteredFindings()` - Filtered findings
- `getFindingsByDataStore()` - Findings by data store
- `getRegexPatternsMatched()` - Regex patterns matched
- `getNewFindingsPerScan()` - New findings per scan

### Reports
- `generateRiskReport()` - Generate risk report
- `generateComplianceReport()` - Generate compliance report
- `generateDatabaseReport()` - Generate database report

## 🔄 Example Component Implementation

```javascript
import React, { useState, useEffect } from 'react';
import riskAssessmentAPI from '../utils/riskAssessmentAPI';

const RiskDashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const clientId = getCurrentUser().client_id;
        
        // Use comprehensive loading functions
        const dashboardData = await riskAssessmentAPI.loadDashboardData(clientId);
        const chartData = await riskAssessmentAPI.loadChartData(clientId);
        const metrics = await riskAssessmentAPI.loadMetrics(clientId);
        
        setData({
          ...dashboardData,
          ...chartData,
          ...metrics
        });
      } catch (error) {
        console.error('Error loading dashboard:', error);
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!data) return <div>No data available</div>;

  return (
    <div>
      <h1>Risk Dashboard</h1>
      
      {/* Display metrics */}
      <div className="metrics-grid">
        <div>Total Data Sources: {data.metrics?.totalDataSources?.total_data_sources || 0}</div>
        <div>Total SDEs: {data.metrics?.totalSDEs?.total_sdes || 0}</div>
        <div>High Risk SDEs: {data.metrics?.highRiskSDEs?.high_risk_sdes || 0}</div>
        <div>Risk Score: {data.metrics?.riskScore?.risk_score || 0}</div>
      </div>
      
      {/* Display charts */}
      <div className="charts-container">
        {/* Risk Distribution Chart */}
        <RiskDistributionChart data={data.riskDistribution} />
        
        {/* Sensitivity Categories Chart */}
        <SensitivityChart data={data.sensitivityCategories} />
        
        {/* Trend Analysis Chart */}
        <TrendChart data={data.trendAnalysis} />
      </div>
    </div>
  );
};

export default RiskDashboard;
```

## 🎯 Best Practices

### 1. Always Use Backend Endpoints
```javascript
// ✅ Use backend endpoints
const data = await riskAssessmentAPI.getTotalDataSources(clientId);

// ❌ Don't write SQL queries in frontend
const data = await fetch('/api/query', {
  method: 'POST',
  body: JSON.stringify({ query: 'SELECT COUNT(*) FROM data_stores' })
});
```

### 2. Handle Errors Gracefully
```javascript
try {
  const result = await riskAssessmentAPI.getRiskScore(clientId);
  if (result.success) {
    return result.data;
  } else {
    console.error('API error:', result.error);
    return { risk_score: 0 }; // Fallback
  }
} catch (error) {
  console.error('Network error:', error);
  return { risk_score: 0 }; // Fallback
}
```

### 3. Use Parallel Loading
```javascript
// ✅ Load data in parallel for better performance
const [metrics, dashboard, charts] = await Promise.all([
  riskAssessmentAPI.loadMetrics(clientId),
  riskAssessmentAPI.loadDashboardData(clientId),
  riskAssessmentAPI.loadChartData(clientId)
]);
```

### 4. Use Fallback Data
```javascript
const loadDataWithFallback = async (clientId) => {
  try {
    const data = await riskAssessmentAPI.getAllMetrics(clientId);
    return data.data || getFallbackMetrics();
  } catch (error) {
    console.error('Error loading metrics:', error);
    return getFallbackMetrics();
  }
};
```

## 🔧 Migration Guide

### From SQL Queries to API Endpoints

**Before (SQL in Frontend):**
```javascript
// ❌ Old way with SQL queries
const fetchRiskData = async () => {
  const response = await fetch('/api/query', {
    method: 'POST',
    body: JSON.stringify({
      query: `
        SELECT 
          COUNT(*) as total_sdes,
          COUNT(CASE WHEN sensitivity = 'high' THEN 1 END) as high_risk_sdes,
          AVG(risk_score) as avg_risk_score
        FROM scan_findings 
        WHERE client_id = '${clientId}'
      `
    })
  });
  return response.json();
};
```

**After (Using risk.py Endpoints):**
```javascript
// ✅ New way using risk.py endpoints
const fetchRiskData = async (clientId) => {
  const [totalSDEs, highRiskSDEs, riskScore] = await Promise.all([
    riskAssessmentAPI.getTotalSDEs(clientId),
    riskAssessmentAPI.getHighRiskSDEs(clientId),
    riskAssessmentAPI.getRiskScore(clientId)
  ]);
  
  return {
    total_sdes: totalSDEs.data?.total_sdes || 0,
    high_risk_sdes: highRiskSDEs.data?.high_risk_sdes || 0,
    avg_risk_score: riskScore.data?.risk_score || 0
  };
};
```

## 📝 Summary

- **Never write SQL queries in the frontend**
- **Always use the risk.py endpoints** through `riskAssessmentAPI`
- **Use comprehensive endpoints** when possible for better performance
- **Handle errors gracefully** with fallback data
- **Load data in parallel** for better user experience
- **Use the utility functions** for common data loading patterns

This approach ensures:
- ✅ Security (no SQL injection risks)
- ✅ Performance (optimized backend queries)
- ✅ Maintainability (centralized business logic)
- ✅ Scalability (proper separation of concerns)
- ✅ Error handling (robust fallback mechanisms) 