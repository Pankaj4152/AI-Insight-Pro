# Comprehensive Dashboard & Risk Analysis - Data Sources & Implementation Guide

## Overview
This document outlines all graphs and visualizations implemented in the comprehensive dashboard, detailing data sources, API endpoints, database queries, and implementation details.

## Table of Contents
- [Dashboard Section](#dashboard-section)
- [Risk Analysis Section](#risk-analysis-section)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [Implementation Details](#implementation-details)

---

## Dashboard Section

### 1. Metric Cards

#### 1.1 Total Data Stores
- **Visualization**: Metric Card with Database icon
- **Data Source**: `data_stores` table
- **Query**: `SELECT COUNT(*) FROM data_stores WHERE client_id = ?`
- **API Endpoint**: `/dashboard/total-data-stores/{client_id}`
- **Purpose**: Show the scale of the data environment
- **Interactivity**: Hover for breakdown by store type
- **Implementation**: `fetchTotalDataStores()` in `enhancedDashboardAPI.js`

#### 1.2 Total SDEs (Sensitive Data Elements)
- **Visualization**: Metric Card with FileText icon
- **Data Source**: `sdes` table
- **Query**: `SELECT COUNT(*) FROM sdes WHERE client_id = ?`
- **API Endpoint**: `/dashboard/total-sdes/{client_id}`
- **Purpose**: Indicate number of sensitive elements
- **Interactivity**: Click to view SDE list
- **Implementation**: `fetchTotalSDEs()` in `enhancedDashboardAPI.js`

#### 1.3 High-Risk Findings
- **Visualization**: Metric Card with AlertTriangle icon
- **Data Source**: `scan_findings` table
- **Query**: `SELECT COUNT(*) FROM scan_findings WHERE client_id = ? AND risk_level = 'high'`
- **API Endpoint**: `/dashboard/high-risk-findings/{client_id}`
- **Purpose**: Highlight urgent issues
- **Interactivity**: Click to see recent high-risk findings
- **Implementation**: `fetchHighRiskFindings()` in `enhancedDashboardAPI.js`

#### 1.4 Last Scan Time
- **Visualization**: Metric Card with Clock icon
- **Data Source**: `scan_findings.scan_timestamp` or `scans.scan_timestamp`
- **Query**: `SELECT MAX(scan_timestamp) FROM scan_findings WHERE client_id = ?`
- **API Endpoint**: `/dashboard/last-scan-time/{client_id}`
- **Purpose**: Show recent scanning activity
- **Interactivity**: Hover for scan details
- **Implementation**: `fetchLastScanTime()` in `enhancedDashboardAPI.js`

#### 1.5 Next Scheduled Scan
- **Visualization**: Metric Card with Calendar icon
- **Data Source**: `scan_baselines` table
- **Query**: `SELECT MIN(next_scan_scheduled) FROM scan_baselines WHERE client_id = ?`
- **API Endpoint**: `/dashboard/next-scheduled-scan/{client_id}`
- **Purpose**: Inform users of upcoming scans
- **Interactivity**: Hover for scan frequency
- **Implementation**: `fetchNextScheduledScan()` in `enhancedDashboardAPI.js`

#### 1.6 Overall Risk Score
- **Visualization**: Metric Card with Target icon
- **Data Source**: `risk_assessments` table
- **Query**: `SELECT risk_score FROM risk_assessments WHERE client_id = ? ORDER BY timestamp DESC LIMIT 1`
- **API Endpoint**: `/dashboard/overall-risk-score/{client_id}`
- **Purpose**: Summarize risk level
- **Interactivity**: Click to view risk trend
- **Implementation**: `fetchOverallRiskScore()` in `enhancedDashboardAPI.js`

#### 1.7 Total Sensitive Records
- **Visualization**: Metric Card with Lock icon
- **Data Source**: `risk_assessments` table
- **Query**: `SELECT total_sensitive_records FROM risk_assessments WHERE client_id = ? ORDER BY timestamp DESC LIMIT 1`
- **API Endpoint**: `/dashboard/total-sensitive-records/{client_id}`
- **Purpose**: Show volume of sensitive data
- **Interactivity**: Hover for sensitivity breakdown
- **Implementation**: `fetchTotalSensitiveRecords()` in `enhancedDashboardAPI.js`

#### 1.8 Average Scan Duration
- **Visualization**: Metric Card with Clock icon
- **Data Source**: `scan_baselines` table
- **Query**: `SELECT AVG(last_scan_duration) as avg_scan_duration FROM scan_baselines WHERE client_id = ?`
- **API Endpoint**: `/dashboard/average-scan-duration/{client_id}`
- **Purpose**: Understand scan efficiency
- **Interactivity**: Hover for min/max duration
- **Implementation**: `fetchAverageScanDuration()` in `enhancedDashboardAPI.js`

### 2. Dashboard Charts

#### 2.1 Data Store Types Distribution
- **Visualization**: Pie Chart
- **Data Source**: `data_stores` table
- **Query**: `SELECT store_type, COUNT(*) FROM data_stores WHERE client_id = ? GROUP BY store_type`
- **API Endpoint**: `/dashboard/data-store-types/{client_id}`
- **Purpose**: Show distribution of storage types
- **Interactivity**: Click segments to filter findings by store type
- **Implementation**: `fetchDataStoreTypesDistribution()` in `enhancedDashboardAPI.js`
- **Chart Component**: Pie chart in `ComprehensiveDashboard.js`

#### 2.2 Top 5 SDEs by Findings
- **Visualization**: Bar Chart
- **Data Source**: `scan_findings` + `sdes` tables (JOIN)
- **Query**: `SELECT s.dataset_name, COUNT(*) as finding_count FROM scan_findings sf JOIN sdes s ON sf.sde_id = s.sde_id WHERE sf.client_id = ? GROUP BY s.dataset_name ORDER BY finding_count DESC LIMIT 5`
- **API Endpoint**: `/dashboard/top-sdes-by-findings/{client_id}`
- **Purpose**: Prioritize risky SDEs
- **Interactivity**: Click bars to view detailed findings
- **Implementation**: `fetchTop5SDEsByFindings()` in `enhancedDashboardAPI.js`
- **Chart Component**: Bar chart in `ComprehensiveDashboard.js`

#### 2.3 Risk Score Over Time
- **Visualization**: Line Chart
- **Data Source**: `risk_assessments` table
- **Query**: `SELECT timestamp, risk_score FROM risk_assessments WHERE client_id = ? ORDER BY timestamp`
- **API Endpoint**: `/dashboard/risk-score-timeline/{client_id}?days={days}`
- **Purpose**: Track risk trends
- **Interactivity**: Zoom into time ranges, filter by period
- **Implementation**: `fetchRiskScoreOverTime()` in `enhancedDashboardAPI.js`
- **Chart Component**: Line chart in `ComprehensiveDashboard.js`

#### 2.4 Scan History
- **Visualization**: Line Chart
- **Data Source**: `scans` table
- **Query**: `SELECT DATE(scan_timestamp), COUNT(*) as scan_count FROM scans WHERE client_id = ? GROUP BY DATE(scan_timestamp) ORDER BY DATE(scan_timestamp)`
- **API Endpoint**: `/dashboard/scan-history/{client_id}?days={days}`
- **Purpose**: Track scanning frequency
- **Interactivity**: Filter by date range, hover for scan details
- **Implementation**: `fetchScanHistory()` in `enhancedDashboardAPI.js`
- **Chart Component**: Line chart in `ComprehensiveDashboard.js`

#### 2.5 New Findings per Scan
- **Visualization**: Bar Chart
- **Data Source**: `scan_findings` + `scans` tables (JOIN)
- **Query**: `SELECT s.scan_id, COUNT(*) as new_findings FROM scan_findings sf JOIN scans s ON sf.scan_id = s.scan_id WHERE sf.client_id = ? GROUP BY s.scan_id ORDER BY s.scan_timestamp`
- **API Endpoint**: `/dashboard/new-findings-per-scan/{client_id}`
- **Purpose**: Monitor issue trends
- **Interactivity**: Filter by risk level, click for findings
- **Implementation**: `fetchNewFindingsPerScan()` in `enhancedDashboardAPI.js`
- **Chart Component**: Bar chart in `ComprehensiveDashboard.js`

#### 2.6 Compliance Summary
- **Visualization**: Gauge/Progress Bar + Breakdown
- **Data Source**: `compliance` + `sdes` tables (JOIN)
- **Query**: `SELECT (COUNT(CASE WHEN status = 'compliant' THEN 1 END) * 100.0) / COUNT(*) as compliance_percentage FROM compliance WHERE sde_id IN (SELECT sde_id FROM sdes WHERE client_id = ?)`
- **API Endpoint**: `/dashboard/compliance-summary/{client_id}`
- **Purpose**: Quick compliance overview
- **Interactivity**: Click to view policy details
- **Implementation**: `fetchComplianceSummary()` in `enhancedDashboardAPI.js`
- **Chart Component**: Custom compliance widget in `ComprehensiveDashboard.js`

#### 2.7 Model Registry Metrics
- **Visualization**: Metric Card + Pie Chart
- **Data Source**: `model_inventory` table
- **Query**: `SELECT COUNT(*) as total_models FROM model_inventory WHERE client_id = ?` or `SELECT provider_name, COUNT(*) FROM model_inventory WHERE client_id = ? GROUP BY provider_name`
- **API Endpoint**: `/dashboard/model-registry-metrics/{client_id}`
- **Purpose**: View model usage (optional)
- **Interactivity**: Click to see model details
- **Implementation**: `fetchModelRegistryMetrics()` in `enhancedDashboardAPI.js`
- **Chart Component**: Model metrics widget in `ComprehensiveDashboard.js`

#### 2.8 Recent High-Risk Findings
- **Visualization**: Alert List
- **Data Source**: `scan_findings` table
- **Query**: `SELECT finding_id, sde_id, risk_level, scan_timestamp FROM scan_findings WHERE client_id = ? AND risk_level = 'high' ORDER BY scan_timestamp DESC LIMIT 5`
- **API Endpoint**: `/dashboard/recent-high-risk-findings/{client_id}?limit={limit}`
- **Purpose**: Alert users to urgent issues
- **Interactivity**: Click to view finding details
- **Implementation**: `fetchRecentHighRiskFindings()` in `enhancedDashboardAPI.js`
- **Chart Component**: Recent findings list in `ComprehensiveDashboard.js`

---

## Risk Analysis Section

### 3. Risk Analysis Charts

#### 3.1 Risk Distribution
- **Visualization**: Pie Chart
- **Data Source**: `scan_findings` table
- **Query**: `SELECT risk_level, COUNT(*) FROM scan_findings WHERE client_id = ? GROUP BY risk_level`
- **API Endpoint**: `/risk-analysis/risk-distribution/{client_id}`
- **Purpose**: Understand risk profile
- **Interactivity**: Click segments to filter findings
- **Implementation**: `fetchRiskDistribution()` in `enhancedDashboardAPI.js`
- **Chart Component**: Pie chart in `ComprehensiveDashboard.js`

#### 3.2 Compliance Status by Policy
- **Visualization**: Bar Chart
- **Data Source**: `compliance` + `dp_policies` + `sdes` tables (JOIN)
- **Query**: `SELECT p.policy_name, c.status, COUNT(*) as count FROM compliance c JOIN dp_policies p ON c.policy_id = p.policy_id WHERE c.sde_id IN (SELECT sde_id FROM sdes WHERE client_id = ?) GROUP BY p.policy_name, c.status`
- **API Endpoint**: `/risk-analysis/compliance-by-policy/{client_id}`
- **Purpose**: Identify compliance gaps
- **Interactivity**: Filter by policy, click for details
- **Implementation**: `fetchComplianceStatusByPolicy()` in `enhancedDashboardAPI.js`
- **Chart Component**: Bar chart in `ComprehensiveDashboard.js`

#### 3.3 Findings by Data Store
- **Visualization**: Bar Chart
- **Data Source**: `scan_findings` + `scans` + `data_stores` tables (JOIN)
- **Query**: `SELECT ds.store_name, COUNT(*) as finding_count FROM scan_findings sf JOIN scans s ON sf.scan_id = s.scan_id JOIN data_stores ds ON s.store_id = ds.store_id WHERE sf.client_id = ? GROUP BY ds.store_name`
- **API Endpoint**: `/risk-analysis/findings-by-data-store/{client_id}`
- **Purpose**: Prioritize data stores
- **Interactivity**: Click bars to filter findings
- **Implementation**: `fetchFindingsByDataStore()` in `enhancedDashboardAPI.js`
- **Chart Component**: Bar chart in `ComprehensiveDashboard.js`

#### 3.4 Sensitivity Distribution
- **Visualization**: Pie Chart
- **Data Source**: `scan_findings` table
- **Query**: `SELECT sensitivity, COUNT(*) FROM scan_findings WHERE client_id = ? GROUP BY sensitivity`
- **API Endpoint**: `/risk-analysis/sensitivity-distribution/{client_id}`
- **Purpose**: Understand sensitive data types
- **Interactivity**: Click segments to filter findings
- **Implementation**: `fetchSensitivityDistribution()` in `enhancedDashboardAPI.js`
- **Chart Component**: Pie chart in `ComprehensiveDashboard.js`

#### 3.5 Detailed Findings Table
- **Visualization**: Interactive Table
- **Data Source**: `scan_findings` + `sdes` + `data_stores` + `scans` tables (JOIN)
- **Query**: `SELECT sf.finding_id, ds.store_name, s.dataset_name, sf.risk_level, sf.sensitivity, sf.finding_type, sf.scan_timestamp FROM scan_findings sf JOIN scans sc ON sf.scan_id = sc.scan_id JOIN data_stores ds ON sc.store_id = ds.store_id JOIN sdes s ON sf.sde_id = s.sde_id WHERE sf.client_id = ?`
- **API Endpoint**: `/risk-analysis/detailed-findings/{client_id}?{filters}`
- **Purpose**: Explore specific findings
- **Interactivity**: Filters for risk level, store, SDE; export CSV/PDF
- **Implementation**: `fetchDetailedFindingsTable()` in `enhancedDashboardAPI.js`
- **Chart Component**: Enhanced table component (separate file)

#### 3.6 Risk Heatmap
- **Visualization**: Heatmap/Matrix
- **Data Source**: `scan_findings` + `sdes` tables (JOIN)
- **Query**: `SELECT s.dataset_name, sf.risk_level, COUNT(*) as finding_count FROM scan_findings sf JOIN sdes s ON sf.sde_id = s.sde_id WHERE sf.client_id = ? GROUP BY s.dataset_name, sf.risk_level`
- **API Endpoint**: `/risk-analysis/risk-heatmap/{client_id}`
- **Purpose**: Identify high-risk areas
- **Interactivity**: Click cells for detailed findings
- **Implementation**: `fetchRiskHeatmapData()` in `enhancedDashboardAPI.js`
- **Chart Component**: Custom heatmap component

#### 3.7 Finding Persistence Timeline
- **Visualization**: Timeline Chart
- **Data Source**: `scan_findings` table
- **Query**: `SELECT finding_id, MIN(scan_timestamp) as first_detected, MAX(scan_timestamp) as last_seen FROM scan_findings WHERE client_id = ? GROUP BY finding_id`
- **API Endpoint**: `/risk-analysis/finding-persistence-timeline/{client_id}`
- **Purpose**: Track persistent issues
- **Interactivity**: Zoom into time ranges, filter by risk level
- **Implementation**: `fetchFindingPersistenceTimeline()` in `enhancedDashboardAPI.js`
- **Chart Component**: Timeline chart component

#### 3.8 Finding Type Breakdown
- **Visualization**: Pie Chart/Bar Chart
- **Data Source**: `scan_findings` table
- **Query**: `SELECT finding_type, COUNT(*) as count FROM scan_findings WHERE client_id = ? GROUP BY finding_type`
- **API Endpoint**: `/risk-analysis/finding-type-breakdown/{client_id}`
- **Purpose**: Understand risk nature
- **Interactivity**: Click segments to filter findings
- **Implementation**: `fetchFindingTypeBreakdown()` in `enhancedDashboardAPI.js`
- **Chart Component**: Doughnut chart in `ComprehensiveDashboard.js`

#### 3.9 Compliance Trends Over Time
- **Visualization**: Line Chart
- **Data Source**: `compliance` + `sdes` tables (JOIN)
- **Query**: `SELECT audit_date, policy_id, status, COUNT(*) as count FROM compliance WHERE sde_id IN (SELECT sde_id FROM sdes WHERE client_id = ?) GROUP BY audit_date, policy_id, status ORDER BY audit_date`
- **API Endpoint**: `/risk-analysis/compliance-trends/{client_id}?days={days}`
- **Purpose**: Track compliance changes
- **Interactivity**: Filter by policy, zoom into time ranges
- **Implementation**: `fetchComplianceTrendsOverTime()` in `enhancedDashboardAPI.js`
- **Chart Component**: Line chart in `ComprehensiveDashboard.js`

#### 3.10 Connection Status Overview
- **Visualization**: Bar Chart
- **Data Source**: `client_connection_history` + `client_connections` tables (JOIN)
- **Query**: `SELECT connection_status, COUNT(*) as count FROM client_connection_history WHERE cli_conn_id IN (SELECT cli_conn_id FROM client_connections WHERE client_id = ?) GROUP BY connection_status`
- **API Endpoint**: `/risk-analysis/connection-status/{client_id}`
- **Purpose**: Monitor connection health
- **Interactivity**: Click to view connection details
- **Implementation**: `fetchConnectionStatusOverview()` in `enhancedDashboardAPI.js`
- **Chart Component**: Bar chart in `ComprehensiveDashboard.js`

#### 3.11 Protection Methods Used
- **Visualization**: Pie Chart
- **Data Source**: `protection` + `sdes` tables (JOIN)
- **Query**: `SELECT p.method, COUNT(*) as count FROM protection p WHERE p.sde_id IN (SELECT sde_id FROM sdes WHERE client_id = ?) GROUP BY p.method`
- **API Endpoint**: `/risk-analysis/protection-methods/{client_id}`
- **Purpose**: Understand protection strategies
- **Interactivity**: Click segments for details
- **Implementation**: `fetchProtectionMethodsUsed()` in `enhancedDashboardAPI.js`
- **Chart Component**: Pie chart in `ComprehensiveDashboard.js`

#### 3.12 Regex Patterns Matched
- **Visualization**: Bar Chart
- **Data Source**: `scan_findings` table
- **Query**: `SELECT pattern_matched, COUNT(*) as count FROM scan_findings WHERE client_id = ? GROUP BY pattern_matched`
- **API Endpoint**: `/risk-analysis/regex-patterns-matched/{client_id}`
- **Purpose**: Identify common patterns in findings
- **Interactivity**: Click bars for matching findings
- **Implementation**: `fetchRegexPatternsMatched()` in `enhancedDashboardAPI.js`
- **Chart Component**: Bar chart in `ComprehensiveDashboard.js`

#### 3.13 PII Catalog Summary
- **Visualization**: Metric Card/Table
- **Data Source**: `pii_catalog` + `sdes` tables (JOIN)
- **Query**: `SELECT compliance_status, risk_level, COUNT(*) FROM pii_catalog WHERE sde_id IN (SELECT sde_id FROM sdes WHERE client_id = ?) GROUP BY compliance_status, risk_level`
- **API Endpoint**: `/risk-analysis/pii-catalog-summary/{client_id}`
- **Purpose**: Summarize PII compliance
- **Interactivity**: Click to view detailed catalog entries
- **Implementation**: `fetchPIICatalogSummary()` in `enhancedDashboardAPI.js`
- **Chart Component**: PII summary widget in `ComprehensiveDashboard.js`

#### 3.14 Regulatory Report Status
- **Visualization**: Bar Chart
- **Data Source**: `regulatory_reporting` + `compliance` + `sdes` tables (JOIN)
- **Query**: `SELECT r.submit_date, COUNT(*) as count FROM regulatory_reporting r JOIN compliance c ON r.compliance_id = c.compliance_id WHERE c.sde_id IN (SELECT sde_id FROM sdes WHERE client_id = ?) GROUP BY r.submit_date`
- **API Endpoint**: `/risk-analysis/regulatory-report-status/{client_id}`
- **Purpose**: Track regulatory submissions
- **Interactivity**: Filter by date, click for report details
- **Implementation**: `fetchRegulatoryReportStatus()` in `enhancedDashboardAPI.js`
- **Chart Component**: Line chart in `ComprehensiveDashboard.js`

---

## API Endpoints

### Dashboard Endpoints
- `GET /dashboard/total-data-stores/{client_id}` - Total data stores count
- `GET /dashboard/total-sdes/{client_id}` - Total SDEs count
- `GET /dashboard/high-risk-findings/{client_id}` - High-risk findings count
- `GET /dashboard/last-scan-time/{client_id}` - Last scan timestamp
- `GET /dashboard/next-scheduled-scan/{client_id}` - Next scheduled scan
- `GET /dashboard/overall-risk-score/{client_id}` - Current risk score
- `GET /dashboard/total-sensitive-records/{client_id}` - Sensitive records count
- `GET /dashboard/average-scan-duration/{client_id}` - Average scan duration
- `GET /dashboard/data-store-types/{client_id}` - Data store types distribution
- `GET /dashboard/top-sdes-by-findings/{client_id}` - Top SDEs by findings
- `GET /dashboard/risk-score-timeline/{client_id}?days={days}` - Risk score timeline
- `GET /dashboard/scan-history/{client_id}?days={days}` - Scan history
- `GET /dashboard/new-findings-per-scan/{client_id}` - New findings per scan
- `GET /dashboard/compliance-summary/{client_id}` - Compliance summary
- `GET /dashboard/model-registry-metrics/{client_id}` - Model registry metrics
- `GET /dashboard/recent-high-risk-findings/{client_id}?limit={limit}` - Recent high-risk findings

### Risk Analysis Endpoints
- `GET /risk-analysis/risk-distribution/{client_id}` - Risk level distribution
- `GET /risk-analysis/compliance-by-policy/{client_id}` - Compliance by policy
- `GET /risk-analysis/findings-by-data-store/{client_id}` - Findings by data store
- `GET /risk-analysis/sensitivity-distribution/{client_id}` - Sensitivity distribution
- `GET /risk-analysis/detailed-findings/{client_id}?{filters}` - Detailed findings table
- `GET /risk-analysis/risk-heatmap/{client_id}` - Risk heatmap data
- `GET /risk-analysis/finding-persistence-timeline/{client_id}` - Finding persistence timeline
- `GET /risk-analysis/finding-type-breakdown/{client_id}` - Finding type breakdown
- `GET /risk-analysis/compliance-trends/{client_id}?days={days}` - Compliance trends
- `GET /risk-analysis/connection-status/{client_id}` - Connection status overview
- `GET /risk-analysis/protection-methods/{client_id}` - Protection methods used
- `GET /risk-analysis/regex-patterns-matched/{client_id}` - Regex patterns matched
- `GET /risk-analysis/pii-catalog-summary/{client_id}` - PII catalog summary
- `GET /risk-analysis/regulatory-report-status/{client_id}` - Regulatory report status

---

## Database Schema

### Core Tables
1. **data_stores** - Data source information
   - `store_id`, `client_id`, `store_name`, `store_type`, `connection_status`

2. **sdes** - Sensitive Data Elements
   - `sde_id`, `client_id`, `dataset_name`, `store_id`, `sensitivity_level`

3. **scan_findings** - Scan results and findings
   - `finding_id`, `client_id`, `sde_id`, `scan_id`, `risk_level`, `sensitivity`, `finding_type`, `scan_timestamp`, `confidence_score`, `detection_method`, `pattern_matched`, `data_value`, `object_path`, `privacy_implications`

4. **scans** - Scan execution records
   - `scan_id`, `client_id`, `store_id`, `scan_timestamp`, `scan_duration`, `status`

5. **risk_assessments** - Risk assessment results
   - `assessment_id`, `client_id`, `timestamp`, `risk_score`, `total_sensitive_records`

6. **compliance** - Compliance monitoring
   - `compliance_id`, `sde_id`, `policy_id`, `status`, `audit_date`

7. **dp_policies** - Data protection policies
   - `policy_id`, `policy_name`, `description`, `category`

8. **scan_baselines** - Scan scheduling and performance
   - `baseline_id`, `client_id`, `last_scan_duration`, `next_scan_scheduled`

9. **model_inventory** - AI/ML model registry
   - `model_id`, `client_id`, `provider_name`, `model_name`, `status`

10. **pii_catalog** - PII catalog entries
    - `catalog_id`, `sde_id`, `compliance_status`, `risk_level`, `category`

11. **protection** - Data protection methods
    - `protection_id`, `sde_id`, `method`, `status`

12. **regulatory_reporting** - Regulatory reporting
    - `report_id`, `compliance_id`, `submit_date`, `status`

13. **client_connections** - Client connection info
    - `cli_conn_id`, `client_id`, `connection_type`

14. **client_connection_history** - Connection history
    - `history_id`, `cli_conn_id`, `connection_status`, `timestamp`

---

## Implementation Details

### File Structure
```
src/
├── components/
│   └── dashboard/
│       └── ComprehensiveDashboard.js    # Main dashboard component
├── utils/
│   ├── enhancedDashboardAPI.js          # API utilities
│   └── enhancedMockDataComplete.js      # Complete mock data
├── Css/
│   └── ComprehensiveDashboard.css       # Dashboard styles
└── pages/
    └── NewRiskAssessmentPage.js         # Updated main page
```

### Key Features
- **Responsive Design**: All charts adapt to different screen sizes
- **Interactive Elements**: Hover effects, click handlers, and filtering
- **Real-time Updates**: Data refreshes automatically
- **Export Capabilities**: CSV/PDF export for tables and charts
- **Dark Mode Support**: CSS variables for theme switching
- **Loading States**: Skeleton loaders and spinner animations
- **Error Handling**: Graceful error handling with retry mechanisms

### Chart Libraries
- **Chart.js**: Primary charting library with react-chartjs-2 wrapper
- **Lucide React**: Icon library for consistent iconography
- **Custom Components**: Specialized widgets for complex visualizations

### Performance Optimizations
- **Lazy Loading**: Components load only when needed
- **Memoization**: React.useMemo for expensive calculations
- **API Batching**: Parallel API calls with Promise.allSettled
- **Data Caching**: Local storage for frequently accessed data

---

## Graph Locations

All graphs are displayed in the **NewRiskAssessmentPage** component with the following tab structure:

1. **Overview Tab**: Basic metrics and key charts
2. **Comprehensive Dashboard Tab**: All dashboard section graphs (metrics + 8 charts)
3. **Detailed Analysis Tab**: Original detailed analysis charts
4. **Risk Findings Tab**: Enhanced findings table
5. **Trends & Activity Tab**: Risk analysis section graphs (14 charts)

The comprehensive dashboard provides a total of **22 unique visualizations** plus **8 metric cards**, giving users a complete view of their data security posture.
