# Risk Assessment Data Sources and Chart Implementation

This document outlines how each graph and visualization in the Risk Assessment Dashboard gets its data from the APIs and database.

## API Configuration

- **Base URL**: Configured in `apiConfig.js`
- **Authentication**: Client ID based multi-tenant access
- **Data Format**: JSON responses from Python FastAPI backend

## Dashboard Section Charts

### 1. Total Data Stores (Metric Card)
- **API Endpoint**: `/risk/total-data-sources/{client_id}`
- **Database Query**: `SELECT COUNT(*) FROM data_stores WHERE client_id = ?`
- **Data Source**: `data_stores` table
- **Implementation**: `fetchTotalDataSources()`
- **Update Frequency**: Real-time on page load and refresh

### 2. Total SDEs (Metric Card)
- **API Endpoint**: `/risk/total-sdes/{client_id}`
- **Database Query**: `SELECT COUNT(*) FROM sdes WHERE client_id = ?`
- **Data Source**: `sdes` table
- **Implementation**: `fetchTotalSDEs()`
- **Update Frequency**: Real-time on page load and refresh

### 3. High-Risk Findings (Metric Card)
- **API Endpoint**: `/risk/high-risk-sdes/{client_id}`
- **Database Query**: `SELECT COUNT(*) FROM scan_findings WHERE client_id = ? AND risk_level = 'high'`
- **Data Source**: `scan_findings` table
- **Implementation**: `fetchHighRiskFindings()`
- **Update Frequency**: Real-time on page load and refresh

### 4. Last Scan Time (Metric Card)
- **API Endpoint**: `/risk/last-scan-time/{client_id}`
- **Database Query**: `SELECT MAX(scan_timestamp) FROM scan_findings WHERE client_id = ?`
- **Data Source**: `scan_findings` or `scans` table
- **Implementation**: `fetchLastScanTime()`
- **Update Frequency**: Real-time on page load and refresh

### 5. Overall Risk Score (Metric Card)
- **API Endpoint**: `/risk/risk-score/{client_id}`
- **Database Query**: `SELECT risk_score FROM risk_assessments WHERE client_id = ? ORDER BY timestamp DESC LIMIT 1`
- **Data Source**: `risk_assessments` table
- **Implementation**: `fetchRiskScore()`
- **Update Frequency**: Real-time on page load and refresh

### 6. Data Store Types (Pie Chart)
- **API Endpoint**: `/risk/data-source-types/{client_id}`
- **Database Query**: `SELECT store_type, COUNT(*) FROM data_stores WHERE client_id = ? GROUP BY store_type`
- **Data Source**: `data_stores` table
- **Chart Type**: Pie Chart using Chart.js
- **Implementation**: `fetchDataStoreTypes()`

### 7. Risk Score Over Time (Line Chart)
- **API Endpoint**: `/risk/trend-analysis/{client_id}?days=30`
- **Database Query**: `SELECT timestamp, risk_score FROM risk_assessments WHERE client_id = ? ORDER BY timestamp`
- **Data Source**: `risk_assessments` table
- **Chart Type**: Line Chart using Chart.js
- **Implementation**: `fetchTrendAnalysis()`

### 8. Scan History (Line Chart)
- **API Endpoint**: `/risk/scan-activity-timeline/{client_id}?days=30`
- **Database Query**: `SELECT DATE(scan_timestamp), COUNT(*) as scan_count FROM scans WHERE client_id = ? GROUP BY DATE(scan_timestamp)`
- **Data Source**: `scans` table
- **Chart Type**: Line Chart using Chart.js
- **Implementation**: `fetchScanActivity()`

## Risk Analysis Section Charts

### 9. Risk Distribution (Pie Chart)
- **API Endpoint**: `/risk/risk-level-distribution/{client_id}`
- **Database Query**: `SELECT risk_level, COUNT(*) FROM scan_findings WHERE client_id = ? GROUP BY risk_level`
- **Data Source**: `scan_findings` table
- **Chart Type**: Doughnut Chart using Chart.js
- **Implementation**: `fetchRiskDistribution()`

### 10. Sensitivity Distribution (Pie Chart)
- **API Endpoint**: `/risk/sensitivity-categories/{client_id}`
- **Database Query**: `SELECT sensitivity, COUNT(*) FROM scan_findings WHERE client_id = ? GROUP BY sensitivity`
- **Data Source**: `scan_findings` table
- **Chart Type**: Pie Chart using Chart.js
- **Implementation**: `fetchSensitivityDistribution()`

### 11. SDE Categories Distribution (Pie Chart)
- **API Endpoint**: `/risk/sde-category-distribution/{client_id}`
- **Database Query**: Complex join between `scan_findings`, `sdes`, and other tables
- **Data Source**: `scan_findings`, `sdes` tables
- **Chart Type**: Pie Chart using Chart.js
- **Implementation**: `fetchSDECategories()`

### 12. Detection Methods (Bar Chart)
- **API Endpoint**: `/risk/detection-method-stats/{client_id}`
- **Database Query**: `SELECT detection_method, COUNT(*) FROM scan_findings WHERE client_id = ? GROUP BY detection_method`
- **Data Source**: `scan_findings` table
- **Chart Type**: Bar Chart using Chart.js
- **Implementation**: `fetchDetectionMethods()`

### 13. Confidence Score Distribution (Bar Chart)
- **API Endpoint**: `/risk/confidence-score-distribution/{client_id}`
- **Database Query**: `SELECT confidence_level, COUNT(*) FROM scan_findings WHERE client_id = ? GROUP BY confidence_level`
- **Data Source**: `scan_findings` table
- **Chart Type**: Bar Chart using Chart.js
- **Implementation**: `fetchConfidenceDistribution()`

### 14. Top Risk Locations (Bar Chart)
- **API Endpoint**: `/risk/top-risk-locations/{client_id}?limit=10`
- **Database Query**: Complex join between `scan_findings`, `scans`, `data_stores`
- **Data Source**: `scan_findings`, `scans`, `data_stores` tables
- **Chart Type**: Horizontal Bar Chart using Chart.js
- **Implementation**: `fetchTopRiskLocations()`

### 15. Findings by Data Store (Bar Chart)
- **API Endpoint**: Custom endpoint needed - `/risk/findings-by-store/{client_id}`
- **Database Query**: 
  ```sql
  SELECT ds.store_name, COUNT(*) as finding_count 
  FROM scan_findings sf 
  JOIN scans s ON sf.scan_id = s.scan_id 
  JOIN data_stores ds ON s.store_id = ds.store_id 
  WHERE sf.client_id = ? 
  GROUP BY ds.store_name
  ```
- **Data Source**: `scan_findings`, `scans`, `data_stores` tables
- **Chart Type**: Bar Chart using Chart.js

### 16. Finding Types Breakdown (Pie Chart)
- **API Endpoint**: Custom endpoint needed - `/risk/finding-types/{client_id}`
- **Database Query**: `SELECT finding_type, COUNT(*) FROM scan_findings WHERE client_id = ? GROUP BY finding_type`
- **Data Source**: `scan_findings` table
- **Chart Type**: Pie Chart using Chart.js

### 17. Top Risk Findings (Enhanced Table)
- **API Endpoint**: `/risk/top-findings/{client_id}?limit=20`
- **Database Query**: Complex query with joins for detailed finding information
- **Data Source**: `scan_findings`, `sdes`, `data_stores`, `scans` tables
- **Component**: Enhanced table with sorting, filtering, and pagination
- **Implementation**: `EnhancedTopRiskFindings` component

## Additional Metrics and Components

### 18. Compliance Summary (Progress Bars)
- **API Endpoint**: Custom endpoint needed - `/risk/compliance-summary/{client_id}`
- **Database Query**: 
  ```sql
  SELECT 
    (COUNT(CASE WHEN status = 'compliant' THEN 1 END) * 100.0) / COUNT(*) as compliance_percentage 
  FROM compliance 
  WHERE sde_id IN (SELECT sde_id FROM sdes WHERE client_id = ?)
  ```
- **Data Source**: `compliance`, `sdes` tables

### 19. Privacy Impact Analysis (Pie Chart)
- **API Endpoint**: `/risk/privacy-violation-types/{client_id}`
- **Database Query**: `SELECT privacy_implications, COUNT(*) FROM scan_findings WHERE client_id = ? GROUP BY privacy_implications`
- **Data Source**: `scan_findings` table

### 20. Risk Matrix Visualization (Heatmap)
- **API Endpoint**: `/risk/risk-matrix-data/{client_id}`
- **Database Query**: Risk likelihood vs impact matrix
- **Data Source**: `scan_findings` table
- **Chart Type**: Custom heatmap using Chart.js matrix

## Data Flow Summary

```
Frontend Component → API Call → FastAPI Backend → Database Query → JSON Response → Chart.js Visualization
```

### Example Data Flow:
1. **User loads page** → `NewRiskAssessmentPage` component mounts
2. **Component calls** → `fetchRiskDistribution(clientId)`
3. **API request** → `GET /risk/risk-level-distribution/{client_id}`
4. **Backend query** → `SELECT risk_level, COUNT(*) FROM scan_findings WHERE client_id = ? GROUP BY risk_level`
5. **Database returns** → `[{risk_level: 'high', count: 45}, {risk_level: 'medium', count: 23}]`
6. **API responds** → `{"risk_distribution": [...]}`
7. **Frontend processes** → Chart.js renders pie chart

## Mock Data Implementation

When `USE_MOCK_DATA = true`, all API calls are bypassed and predefined mock data is used:

- **Mock Data Location**: `src/utils/mockData.js`
- **Mock Data Structure**: Matches API response format exactly
- **Development Benefits**: Allows frontend development without backend dependency
- **Testing**: Consistent data for UI testing and design

## Error Handling

- **API Failures**: Graceful fallback to previous data or empty states
- **Network Issues**: Retry mechanism with exponential backoff
- **Data Validation**: Client-side validation of API responses
- **User Feedback**: Toast notifications for success/error states

## Performance Optimizations

- **Parallel API Calls**: Multiple endpoints called simultaneously using `Promise.allSettled()`
- **Data Caching**: Results cached for filter operations
- **Lazy Loading**: Charts rendered only when tab is active
- **Memoization**: Chart data memoized to prevent unnecessary re-renders

## Update Frequency

- **Real-time Data**: Metrics and finding counts
- **Trend Data**: Updated every 15 minutes
- **Historical Data**: Updated daily
- **Manual Refresh**: User-triggered refresh button available
