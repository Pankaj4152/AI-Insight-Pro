# Risk Assessment API Documentation

This document provides a comprehensive list of all available APIs in `risk.py`, organized by category and functionality.

## Table of Contents
- [Core Risk Assessment APIs](#core-risk-assessment-apis)
- [Individual Metrics APIs](#individual-metrics-apis)
- [Dashboard & Visualization APIs](#dashboard--visualization-apis)
- [Data Analysis APIs](#data-analysis-apis)
- [Report Generation APIs](#report-generation-apis)
- [Database & Utility APIs](#database--utility-apis)
- [Filtering & Search APIs](#filtering--search-apis)

---

## Core Risk Assessment APIs

### POST `/risk/risk-assessment`
**Purpose**: Perform comprehensive risk assessment for a client
- **Method**: POST
- **Request Body**: `RiskAssessmentRequest` (client_id, risk_level, sensitivity, data_source)
- **Response**: Complete risk assessment with all metrics and scores
- **Description**: Main endpoint for conducting risk assessments with optional filtering

### GET `/risk/risk-assessments/{client_id}` working fine
**Purpose**: Retrieve historical risk assessments for a client
- **Method**: GET
- **Parameters**: 
  - `client_id` (path): Client identifier
  - `limit` (query): Number of assessments to return (default: 10)
- **Response**: List of historical risk assessments
- **Description**: Fetches the latest risk assessment records for trend analysis

### GET `/risk/all-metrics/{client_id}`
working fine 

**Purpose**: Get all risk metrics in a single API call
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: Complete metrics object with all risk data
- **Description**: Comprehensive endpoint that returns all metrics and auto-stores assessment data

---

## Individual Metrics APIs

### GET `/risk/total-data-sources/{client_id}`

working fine

**Purpose**: Get count of total data sources for a client
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"client_id": "...", "total_data_sources": number}`

### GET `/risk/total-sdes/{client_id}`
working fine

**Purpose**: Get count of total SDEs (Sensitive Data Elements) for a client
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"client_id": "...", "total_sdes": number}`

### GET `/risk/scanned-sdes/{client_id}`
working fine
**Purpose**: Get count of scanned SDEs for a client
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"client_id": "...", "scanned_sdes": number}`

### GET `/risk/high-risk-sdes/{client_id}`
working fine
**Purpose**: Get count of high-risk SDEs for a client
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"client_id": "...", "high_risk_sdes": number}`

### GET `/risk/high-risk-records/{client_id}`
**Purpose**: Get count of high-risk records for a client
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"client_id": "...", "high_risk_records": number}`

### GET `/risk/total-sensitive-records/{client_id}`
**Purpose**: Get count of total sensitive records for a client
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"client_id": "...", "total_sensitive_records": number}`

### GET `/risk/total-scans/{client_id}`
**Purpose**: Get count of total scans for a client
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"client_id": "...", "total_scans": number}`

### GET `/risk/risk-score/{client_id}`
**Purpose**: Calculate and return risk score for a client
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"client_id": "...", "risk_score": number}`

### GET `/risk/confidence-score/{client_id}`
**Purpose**: Calculate and return confidence score for a client
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"client_id": "...", "confidence_score": number}`

### GET `/risk/last-scan-time/{client_id}`
**Purpose**: Get the last scan time for a client
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"client_id": "...", "last_scan_time": "ISO timestamp"}`

### GET `/risk/next-scheduled-scan/{client_id}`
**Purpose**: Get the next scheduled scan time for a client
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"client_id": "...", "next_scheduled_scan": "ISO timestamp"}`

### GET `/risk/llm-summary/{client_id}`
**Purpose**: Get AI-generated risk summary for a client
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"client_id": "...", "llm_summary": "text"}`

---

## Dashboard & Visualization APIs

### GET `/risk/comprehensive-dashboard/{client_id}`
**Purpose**: Get all dashboard metrics in one call for main dashboard
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: Complete dashboard data including summary, data sources, risk distribution, and sensitivity categories

### GET `/risk/comprehensive-risk-assessment/{client_id}`
**Purpose**: Get all risk assessment visualization data in one call
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: Complete risk assessment data including SDE categories, detection methods, confidence distribution, field types, privacy violations, and risk matrix

### GET `/risk/data-source-types/{client_id}`
**Purpose**: Get distribution of data sources by type for pie chart
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"data_source_types": [{"type": "...", "count": number}]}`

### GET `/risk/risk-level-distribution/{client_id}`
**Purpose**: Get risk level distribution for donut chart
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"risk_distribution": [{"level": "...", "count": number}]}`

### GET `/risk/sensitivity-categories/{client_id}`
**Purpose**: Get sensitivity distribution for pie chart
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"sensitivity_categories": [{"category": "...", "count": number}]}`

### GET `/risk/scan-activity-timeline/{client_id}`
**Purpose**: Get scan activity timeline for line chart
- **Method**: GET
- **Parameters**: 
  - `client_id` (path): Client identifier
  - `days` (query): Number of days to look back (default: 30)
- **Response**: `{"scan_timeline": [{"date": "...", "findings": number}]}`

### GET `/risk/top-risk-locations/{client_id}`
**Purpose**: Get top risk locations for bar chart
- **Method**: GET
- **Parameters**: 
  - `client_id` (path): Client identifier
  - `limit` (query): Number of locations to return (default: 10)
- **Response**: `{"top_risk_locations": [{"store_name": "...", "store_type": "...", "total_risks": number, "high_risks": number}]}`

---

## Data Analysis APIs

### GET `/risk/sde-category-distribution/{client_id}`
**Purpose**: Get SDE categories distribution for pie chart
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"sde_categories": [{"category": "...", "count": number}]}`

### GET `/risk/detection-method-stats/{client_id}`
**Purpose**: Get detection methods statistics for bar chart
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"detection_methods": [{"method": "...", "count": number}]}`

### GET `/risk/confidence-score-distribution/{client_id}`
**Purpose**: Get confidence score distribution for histogram
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"confidence_distribution": [{"level": "...", "count": number}]}`

### GET `/risk/field-type-analysis/{client_id}`
**Purpose**: Get field types analysis for bar chart
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"field_types": [{"type": "...", "count": number}]}`

### GET `/risk/privacy-violation-types/{client_id}`
**Purpose**: Get privacy implications for pie chart
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"privacy_violations": [{"implication": "...", "count": number}]}`

### GET `/risk/risk-matrix-data/{client_id}`
**Purpose**: Get risk matrix data (likelihood vs impact)
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"risk_matrix": [{"likelihood": "...", "impact": "...", "count": number}]}`

### GET `/risk/trend-analysis/{client_id}`
**Purpose**: Get risk trends over time for line chart
- **Method**: GET
- **Parameters**: 
  - `client_id` (path): Client identifier
  - `days` (query): Number of days to analyze (default: 30)
- **Response**: `{"trend_analysis": [{"date": "...", "total_findings": number, "high_risk": number, "medium_risk": number, "low_risk": number}]}`

### GET `/risk/sensitivity-by-source/{client_id}`
**Purpose**: Get sensitivity analysis by data source
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"client_id": "...", "sensitivity_by_source": {"source_name": high_sensitivity_count}}`

---

## Report Generation APIs

### POST `/risk/report`
**Purpose**: Generate risk assessment report
- **Method**: POST
- **Request Body**: `ReportRequest` (client_id, format, name, email, company)
- **Response**: PDF file or HTML content based on format
- **Description**: Generates comprehensive risk assessment reports in PDF or HTML format

### GET `/risk/preview-report`
**Purpose**: Preview risk assessment report as HTML
- **Method**: GET
- **Parameters**: `client_id` (query): Client identifier
- **Response**: HTML content for report preview
- **Description**: Returns HTML preview of the risk assessment report

### GET `/risk/download-report`
**Purpose**: Download risk assessment report as PDF
- **Method**: GET
- **Parameters**: `client_id` (query): Client identifier
- **Response**: PDF file download
- **Description**: Returns PDF file of the risk assessment report

### POST `/risk/generate-database-report`
**Purpose**: Generate comprehensive database infrastructure report
- **Method**: POST
- **Parameters**: `client_id` (query): Client identifier
- **Response**: PDF file of database infrastructure report
- **Description**: Generates detailed database infrastructure analysis report

### POST `/risk/generate-compliance-report`
**Purpose**: Generate compliance and privacy analysis report
- **Method**: POST
- **Parameters**: `client_id` (query): Client identifier
- **Response**: PDF file of compliance report
- **Description**: Generates compliance and privacy impact assessment report

### POST `/risk/cleanup`
**Purpose**: Clean up all report files
- **Method**: POST
- **Response**: Cleanup status
- **Description**: Useful for Docker container maintenance

### POST `/risk/cleanup-html`
**Purpose**: Clean up HTML files older than specified age
- **Method**: POST
- **Parameters**: `max_age_minutes` (query): Maximum age in minutes (default: 5)
- **Response**: Cleanup status
- **Description**: Useful for Docker container maintenance

### POST `/risk/cleanup-all-session-files`
**Purpose**: Clean up all session-related files
- **Method**: POST
- **Response**: Cleanup status
- **Description**: Cleans up all temporary session files and reports

---

## Database & Utility APIs

### GET `/risk/db-status`
**Purpose**: Check database connection status
- **Method**: GET
- **Response**: `{"status": "connected"}` or `{"status": "not connected", "error": "..."}`
- **Description**: Health check endpoint for database connectivity

### GET `/risk/debug-regex-patterns`
**Purpose**: Debug regex patterns and scan findings
- **Method**: GET
- **Response**: Debug information about regex patterns and scan findings
- **Description**: Development/debugging endpoint

### GET `/connections/exists/{client_id}`
**Purpose**: Check if client connections exist
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"exists": boolean}`
- **Description**: Check if client has existing database connections

---

## Modular Report Generation APIs

### GET `/report/preview`
**Purpose**: Preview risk assessment report using modular report generation agent
- **Method**: GET
- **Parameters**: `client_id` (query): Client identifier
- **Response**: HTML content for report preview
- **Description**: Uses modular report generation agent to create HTML preview

### GET `/report/download`
**Purpose**: Download risk assessment report using modular report generation agent
- **Method**: GET
- **Parameters**: `client_id` (query): Client identifier
- **Response**: PDF file download
- **Description**: Uses modular report generation agent to create PDF report

### POST `/report/generate-database-report`
**Purpose**: Generate database infrastructure report using modular agent
- **Method**: POST
- **Parameters**: `client_id` (query): Client identifier
- **Response**: PDF file of database infrastructure report
- **Description**: Uses modular report generation agent for database analysis

### POST `/report/generate-compliance-report`
**Purpose**: Generate compliance report using modular agent
- **Method**: POST
- **Parameters**: `client_id` (query): Client identifier
- **Response**: PDF file of compliance report
- **Description**: Uses modular report generation agent for compliance analysis

### POST `/report/generate-comprehensive-report`
**Purpose**: Generate comprehensive scan report using modular agent
- **Method**: POST
- **Request Body**: `{"scan_id": number, "client_id": "string"}`
- **Response**: Multiple report formats (JSON, HTML, CSV, PDF)
- **Description**: Generates comprehensive reports for specific scan results

### POST `/report/generate-executive-summary`
**Purpose**: Generate executive summary for a scan
- **Method**: POST
- **Request Body**: `{"scan_id": number, "client_id": "string"}`
- **Response**: Executive summary in text format
- **Description**: Creates high-level executive summary of scan findings

### POST `/report/generate-audit-trail`
**Purpose**: Generate audit trail for a scan
- **Method**: POST
- **Request Body**: `{"scan_id": number, "client_id": "string"}`
- **Response**: Audit trail report
- **Description**: Creates detailed audit trail of scan activities

---

## Filtering & Search APIs

### GET `/risk/filtered-findings/`
**Purpose**: Filter SDEs and scan findings by various criteria
- **Method**: GET
- **Parameters**: 
  - `client_id` (query): Client identifier
  - `data_source` (query): Filter by data source
  - `risk_level` (query): Filter by risk level
  - `sensitivity` (query): Filter by sensitivity level
- **Response**: Filtered SDEs and findings with summary statistics

### GET `/risk/top-findings/{client_id}`
**Purpose**: Get top risk findings with specific filters
- **Method**: GET
- **Parameters**: 
  - `client_id` (path): Client identifier
  - `limit` (query): Number of findings to return (default: 7)
  - `sensitivity` (query): Filter by sensitivity level
  - `risk_level` (query): Filter by risk level
- **Response**: Top risk findings with location and type information

### GET `/risk/scan-activity/{client_id}`
**Purpose**: Get scan activity data including recent scans and status
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: Recent scans, daily scan data, data stores, and active sources

### GET `/risk/sde-count/`
**Purpose**: Count SDEs by pattern name and data source
- **Method**: GET
- **Parameters**: 
  - `pattern_name` (query): Regex pattern name
  - `data_source` (query): Data source name
- **Response**: Count of findings matching the pattern in the specified data source

### GET `/risk/dataset-names/{client_id}`
**Purpose**: Get dataset names for a client
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"client_id": "...", "dataset_names": ["..."]}`

### GET `/risk/data-sources/{client_id}`
**Purpose**: Get data sources for a client
- **Method**: GET
- **Parameters**: `client_id` (path): Client identifier
- **Response**: `{"client_id": "...", "data_sources": [{"name": "...", "type": "..."}]}`

---

## API Categories Summary

### **Core Assessment APIs (3 endpoints)**
- Main risk assessment functionality
- Historical data retrieval
- Comprehensive metrics gathering

### **Individual Metrics APIs (11 endpoints)**
- Specific metric retrieval
- Score calculations
- Timestamp information

### **Dashboard & Visualization APIs (7 endpoints)**
- Chart data for dashboards
- Comprehensive dashboard data
- Timeline and location data

### **Data Analysis APIs (7 endpoints)**
- Statistical analysis
- Distribution data
- Trend analysis

### **Report Generation APIs (8 endpoints)**
- PDF and HTML report generation
- Database infrastructure reports
- Compliance and privacy reports
- File cleanup utilities

### **Modular Report Generation APIs (7 endpoints)**
- Advanced report generation using modular agent
- Comprehensive scan reports
- Executive summaries and audit trails
- Multiple report formats (JSON, HTML, CSV, PDF)

### **Database & Utility APIs (3 endpoints)**
- Health checks
- Debugging tools
- Connection verification

### **Filtering & Search APIs (6 endpoints)**
- Data filtering
- Search functionality
- Activity tracking

---

## Total API Count: 47 Endpoints

All APIs follow RESTful conventions and return JSON responses unless specified otherwise (e.g., PDF file downloads). Each API includes proper error handling and logging for debugging purposes.

---

## Report Endpoint Data Sources

### **Risk Assessment Reports**
- **Primary Data**: `risk_assessments` table
- **Query**: `SELECT * FROM risk_assessments WHERE client_id = %s ORDER BY timestamp DESC LIMIT 1`
- **Key Fields**: assessment_id, total_data_sources, total_sdes, scanned_sdes, high_risk_sdes, total_sensitive_records, risk_score, confidence_score, llm_summary

### **Database Infrastructure Reports**
- **Primary Data**: `client_connections`, `data_stores`, `scans`, `scan_baselines` tables
- **Queries**: 
  - Connection summary: `SELECT * FROM client_connections WHERE client_id = %s`
  - Data stores: `SELECT * FROM data_stores WHERE client_id = %s`
  - Scan statistics: `SELECT * FROM scans s JOIN scan_baselines sb ON s.store_id = sb.store_id WHERE ds.client_id = %s`

### **Compliance Reports**
- **Primary Data**: `scan_findings` table
- **Query**: `SELECT * FROM scan_findings WHERE client_id = %s`
- **Key Fields**: sensitivity, sde_category, risk_level, privacy_implications

### **Comprehensive Scan Reports**
- **Primary Data**: `scans`, `scan_findings`, `data_stores` tables
- **Queries**:
  - Scan info: `SELECT * FROM scans WHERE scan_id = %s`
  - Findings: `SELECT * FROM scan_findings WHERE scan_id = %s`
  - Store details: `SELECT * FROM data_stores WHERE store_id = %s`

### **Data Flow Summary**
```
API Endpoint → Report Generation Function → Database Query Functions → PostgreSQL Database
    ↓
Tables: risk_assessments, scan_findings, data_stores, scans, client_connections, scan_baselines
```

All report endpoints use the correct `client_id` column for multi-tenant data isolation and proper error handling for missing data scenarios. 