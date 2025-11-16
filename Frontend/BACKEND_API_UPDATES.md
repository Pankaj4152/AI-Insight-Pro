# Backend API Updates for Existing Database Schema

## Overview
This document provides the necessary updates for backend API endpoints to work with the existing database schema without requiring database changes.

## Database Schema Mapping

### Current Database Fields → Frontend Expected Fields

| Database Field | Frontend Field | Notes |
|----------------|----------------|-------|
| `sensitivity` | `sde_category` | Main category field |
| `dataset_name` + `dataset_column` | `location` | Combined location info |
| `scan_timestamp` | `timestamp` | Timestamp field |
| `findings_count` | `findings` | Count of findings |

## Required API Endpoint Updates

### 1. `/risk/top-findings/{client_id}`

**Current Query (needs update):**
```sql
SELECT 
    sf.finding_id,
    sf.sde_id,
    sf.risk_level,
    sf.confidence_score,
    sf.detection_method,
    sf.scan_timestamp,
    sf.object_path,
    sf.data_value,
    s.sensitivity as sde_category,  -- Map sensitivity to sde_category
    s.dataset_name,
    s.dataset_column
FROM scan_findings sf
JOIN sdes s ON sf.sde_id = s.sde_id
WHERE sf.client_id = $1
ORDER BY sf.confidence_score DESC, sf.scan_timestamp DESC
LIMIT $2;
```

**Response Format:**
```json
{
  "client_id": "3Ty9NjUYEJZdzvgRnpGqU3RzpEl2",
  "findings": [
    {
      "finding_id": "finding_001",
      "sde_category": "PII",  // Map from sensitivity
      "risk_level": "high",
      "location": "customer_db.personal_info",  // Combine dataset_name.dataset_column
      "description": "Sensitive data detected",
      "confidence_score": 95,
      "detection_method": "regex",
      "scan_timestamp": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### 2. `/risk/scan-activity-timeline/{client_id}`

**Current Query (needs update):**
```sql
SELECT 
    s.scan_id,
    s.scan_timestamp as timestamp,  -- Map scan_timestamp to timestamp
    s.status,
    s.scan_duration,
    COUNT(sf.finding_id) as findings_count
FROM scans s
LEFT JOIN scan_findings sf ON s.scan_id = sf.scan_id
WHERE s.client_id = $1 
    AND s.scan_timestamp >= CURRENT_DATE - INTERVAL '$2 days'
GROUP BY s.scan_id, s.scan_timestamp, s.status, s.scan_duration
ORDER BY s.scan_timestamp DESC;
```

**Response Format:**
```json
{
  "timeline": [
    {
      "scan_id": "scan_001",
      "timestamp": "2024-01-15T10:30:00Z",  // Map from scan_timestamp
      "status": "completed",
      "findings_count": 15  // Map from findings_count
    }
  ]
}
```

### 3. `/risk/trend-analysis/{client_id}`

**Current Query (needs update):**
```sql
SELECT 
    DATE(s.scan_timestamp) as date,
    COUNT(sf.finding_id) as total_findings,
    COUNT(CASE WHEN sf.risk_level = 'high' THEN 1 END) as high_risk,
    AVG(sf.confidence_score) as avg_confidence
FROM scans s
LEFT JOIN scan_findings sf ON s.scan_id = sf.scan_id
WHERE s.client_id = $1 
    AND s.scan_timestamp >= CURRENT_DATE - INTERVAL '$2 days'
GROUP BY DATE(s.scan_timestamp)
ORDER BY date DESC;
```

**Response Format:**
```json
{
  "trends": [
    {
      "date": "2024-01-15",
      "total_findings": 25,
      "high_risk": 5,
      "avg_confidence": 85.5
    }
  ]
}
```

### 4. `/risk/comprehensive-dashboard/{client_id}`

**Summary Query:**
```sql
SELECT 
    COUNT(DISTINCT ds.store_id) as total_data_sources,
    COUNT(DISTINCT s.sde_id) as total_sdes,
    COUNT(DISTINCT sc.scan_id) as total_scans,
    COUNT(CASE WHEN sf.risk_level = 'high' THEN 1 END) as high_risk_sdes,
    COUNT(sf.finding_id) as total_sensitive_records,
    AVG(sf.confidence_score) as confidence_score
FROM data_stores ds
LEFT JOIN sdes s ON ds.store_id = s.store_id
LEFT JOIN scans sc ON ds.store_id = sc.store_id
LEFT JOIN scan_findings sf ON sc.scan_id = sf.scan_id
WHERE ds.client_id = $1;
```

**Risk Distribution Query:**
```sql
SELECT 
    sf.risk_level,
    COUNT(*) as count
FROM scan_findings sf
WHERE sf.client_id = $1
GROUP BY sf.risk_level;
```

**SDE Categories Query (using sensitivity):**
```sql
SELECT 
    s.sensitivity as category,  -- Map sensitivity to category
    COUNT(*) as count
FROM scan_findings sf
JOIN sdes s ON sf.sde_id = s.sde_id
WHERE sf.client_id = $1
GROUP BY s.sensitivity;
```

**Response Format:**
```json
{
  "summary": {
    "total_data_sources": 2,
    "total_sdes": 15,
    "total_scans": 8,
    "high_risk_sdes": 3,
    "total_sensitive_records": 25,
    "risk_score": 75,
    "confidence_score": 85.5
  },
  "risk_distribution": [
    {"level": "low", "count": 5},
    {"level": "medium", "count": 10},
    {"level": "high", "count": 8},
    {"level": "critical", "count": 2}
  ],
  "sensitivity_categories": [
    {"category": "PII", "count": 12},
    {"category": "Financial", "count": 8},
    {"category": "Health", "count": 5}
  ]
}
```

## Field Mapping Functions

### Python/JavaScript Field Mapping

```python
def map_database_to_frontend(db_record):
    """Map database fields to frontend expected fields"""
    return {
        # Top Findings mapping
        'sde_category': db_record.get('sensitivity'),
        'location': f"{db_record.get('dataset_name', '')}.{db_record.get('dataset_column', '')}",
        'timestamp': db_record.get('scan_timestamp'),
        'findings': db_record.get('findings_count'),
        
        # Keep original fields as fallback
        'sensitivity': db_record.get('sensitivity'),
        'dataset_name': db_record.get('dataset_name'),
        'dataset_column': db_record.get('dataset_column'),
        'scan_timestamp': db_record.get('scan_timestamp'),
        'findings_count': db_record.get('findings_count'),
        
        # Pass through other fields
        **{k: v for k, v in db_record.items() if k not in ['sensitivity', 'dataset_name', 'dataset_column', 'scan_timestamp', 'findings_count']}
    }
```

```javascript
function mapDatabaseToFrontend(dbRecord) {
  return {
    // Top Findings mapping
    sde_category: dbRecord.sensitivity,
    location: `${dbRecord.dataset_name || ''}.${dbRecord.dataset_column || ''}`,
    timestamp: dbRecord.scan_timestamp,
    findings: dbRecord.findings_count,
    
    // Keep original fields as fallback
    sensitivity: dbRecord.sensitivity,
    dataset_name: dbRecord.dataset_name,
    dataset_column: dbRecord.dataset_column,
    scan_timestamp: dbRecord.scan_timestamp,
    findings_count: dbRecord.findings_count,
    
    // Pass through other fields
    ...Object.fromEntries(
      Object.entries(dbRecord).filter(([key]) => 
        !['sensitivity', 'dataset_name', 'dataset_column', 'scan_timestamp', 'findings_count'].includes(key)
      )
    )
  };
}
```

## Implementation Steps

1. **Update SQL Queries**: Use the corrected queries above
2. **Add Field Mapping**: Apply the mapping functions to transform database results
3. **Test Endpoints**: Verify each endpoint returns the expected format
4. **Update Error Handling**: Ensure proper error messages for missing data

## Testing Checklist

- [ ] `/risk/top-findings/{client_id}` returns findings with `sde_category` field
- [ ] `/risk/scan-activity-timeline/{client_id}` returns timeline with `timestamp` field
- [ ] `/risk/trend-analysis/{client_id}` returns trends with correct date format
- [ ] `/risk/comprehensive-dashboard/{client_id}` returns summary with all required fields
- [ ] All endpoints handle empty results gracefully
- [ ] Error responses include meaningful messages

## Notes

- The frontend has been updated to handle both old and new field names
- Fallback data is provided when API calls fail
- Database schema remains unchanged
- All existing data will continue to work with these updates 