# Data Protection Pipeline API Documentation

This document provides comprehensive documentation for all available API endpoints in the Data Protection Pipeline system.

## Base URL
```
Production: https://agents-1071432896229.asia-south2.run.app
Local: http://localhost:8000
```

## Table of Contents
- [Authentication & Health](#authentication--health)
- [Discovery Endpoints](#discovery-endpoints)
- [Scanning Endpoints](#scanning-endpoints)
- [SDE Management](#sde-management)
- [Discovered Objects](#discovered-objects)
- [Pipeline Orchestration](#pipeline-orchestration)
- [Data Models](#data-models)

---

## Authentication & Health

### Health Check
Check if the API service is running and healthy.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-03T10:30:00.000Z"
}
```

---

## Discovery Endpoints

### Run Discovery for Client
Discover and register data sources for a specific client.

**Endpoint:** `POST /discover`

**Request Body:**
```json
{
  "client_id": "string"
}
```

**Response:**
```json
{
  "status": "success",
  "client_id": "string",
  "action": "discovery",
  "results": {
    "status": "completed",
    "sources_discovered": [],
    "total_sources": 0
  },
  "timestamp": "2025-08-03T10:30:00.000Z"
}
```

### Bulk Discovery for Missing Clients
Run discovery for all clients that have connections but no data_stores entries.

**Endpoint:** `POST /discover-all-missing`

**Response:**
```json
{
  "status": "success",
  "message": "Bulk discovery completed for N clients",
  "clients_processed": 0,
  "successful_discoveries": 0,
  "failed_discoveries": 0,
  "discovery_results": {},
  "errors": [],
  "timestamp": "2025-08-03T10:30:00.000Z"
}
```

---

## Scanning Endpoints

### Scan Latest Database (Intelligent Selective)
Prioritizes scanning files from selected_objects table if available, otherwise falls back to full latest database scan.

**Endpoint:** `POST /scan-latest`

**Request Body:**
```json
{
  "client_id": "string"
}
```

**Response:**
```json
{
  "status": "success",
  "client_id": "string",
  "scan_type": "latest_database_selective|latest_database_full",
  "selective_scan_used": true|false,
  "results": {
    "total_findings": 0,
    "summary": "string"
  },
  "timestamp": "2025-08-03T10:30:00.000Z"
}
```

### Scan All Databases (Force Full Scan)
Ignores selected_objects table and performs a full scan of all databases and files.

**Endpoint:** `POST /scan-all`

**Request Body:**
```json
{
  "client_id": "string"
}
```

**Response:**
```json
{
  "status": "success",
  "client_id": "string",
  "scan_type": "all_databases_full",
  "selective_scan_used": false,
  "message": "Full scan completed - selected objects ignored",
  "results": {
    "total_findings": 0,
    "summary": "string"
  },
  "timestamp": "2025-08-03T10:30:00.000Z"
}
```

### Scan Specific Database
Scan a specific database and optionally specific tables within it.

**Endpoint:** `POST /scan-specific`

**Request Body:**
```json
{
  "client_id": "string",
  "store_name": "string",
  "tables": ["table1", "table2"] // optional
}
```

**Response:**
```json
{
  "status": "success",
  "client_id": "string",
  "scan_type": "specific_database",
  "target_store_name": "string",
  "target_tables": ["string"],
  "results": {
    "total_findings": 0,
    "summary": "string"
  },
  "timestamp": "2025-08-03T10:30:00.000Z"
}
```

### Scan Selected Objects Only (Force Selective)
Scan only the objects explicitly selected in the selected_objects table. Fails if no objects are selected.

**Endpoint:** `POST /scan-selected-only`

**Request Body:**
```json
{
  "client_id": "string"
}
```

**Response:**
```json
{
  "status": "success",
  "client_id": "string",
  "scan_type": "selected_objects_only",
  "selective_scan_used": true,
  "selected_objects_count": 0,
  "message": "Selective scan completed for N selected objects",
  "results": {
    "total_findings": 0,
    "summary": "string"
  },
  "timestamp": "2025-08-03T10:30:00.000Z"
}
```

**Error Response (400):**
```json
{
  "detail": "No objects selected for scanning for client {client_id}. Use /scan-all for full scan or select objects first."
}
```

### List Available Databases
List all available databases for a client.

**Endpoint:** `GET /list-databases/{client_id}`

**Parameters:**
- `client_id` (path): Client ID

**Response:**
```json
{
  "status": "success",
  "client_id": "string",
  "total_databases": 0,
  "databases": [
    {
      "store_name": "string",
      "type": "string",
      "location": "string",
      "project_id": "string",
      "database_name": "string"
    }
  ],
  "timestamp": "2025-08-03T10:30:00.000Z"
}
```

---

## SDE Management

### Get Client SDE Selections
Get the current SDE selections for a client.

**Endpoint:** `GET /client-sdes/{client_id}`

**Parameters:**
- `client_id` (path): Client ID

**Response:**
```json
{
  "client_id": "string",
  "selected_sdes": [
    {
      "pattern_name": "string",
      "sensitivity": "string",
      "protection_method": "string",
      "selected_at": "2025-08-03T10:30:00.000Z"
    }
  ],
  "total_count": 0,
  "timestamp": "2025-08-03T10:30:00.000Z"
}
```

### Update Client SDE Selections
Update SDE selections for a client. This replaces all existing selections.

**Endpoint:** `POST /client-sdes`

**Request Body:**
```json
{
  "client_id": "string",
  "pattern_names": ["email", "phone", "ssn"]
}
```

**Response:**
```json
{
  "status": "success",
  "client_id": "string",
  "selected_sdes": [
    {
      "pattern_name": "string",
      "sensitivity": "medium",
      "protection_method": "encryption",
      "selected_at": "2025-08-03T10:30:00.000Z"
    }
  ],
  "total_count": 0,
  "message": "Updated SDE selections for client {client_id}",
  "timestamp": "2025-08-03T10:30:00.000Z"
}
```

### Get Available SDEs
Get the list of all available SDE patterns that clients can select from.

**Endpoint:** `GET /available-sdes`

**Response:**
```json
{
  "available_sdes": [
    {
      "pattern_name": "email",
      "description": "Pattern for detecting email addresses"
    },
    {
      "pattern_name": "phone",
      "description": "Pattern for detecting phone numbers"
    }
  ],
  "total_count": 0,
  "timestamp": "2025-08-03T10:30:00.000Z"
}
```

---

## Discovered Objects

### Get Discovered Objects
Get discovered objects (files/tables) for a client.

**Endpoint:** `GET /discovered-objects/{client_id}`

**Parameters:**
- `client_id` (path): Client ID
- `store_id` (query, optional): Filter by specific data store
- `limit` (query, optional): Maximum number of objects to return (default: 100)

**Response:**
```json
{
  "status": "success",
  "client_id": "string",
  "total_objects": 0,
  "objects": [
    {
      "object_id": 0,
      "store_id": 0,
      "name": "string",
      "type": "file|table",
      "path": "string",
      "size_bytes": 0,
      "is_accessible": true,
      "last_modified": "2025-08-03T10:30:00.000Z"
    }
  ],
  "objects_by_type": {},
  "objects_by_store": {},
  "timestamp": "2025-08-03T10:30:00.000Z"
}
```

### Get Discovered Objects by Store
Get discovered objects grouped by data store for a client.

**Endpoint:** `GET /discovered-objects/{client_id}/stores`

**Parameters:**
- `client_id` (path): Client ID

**Response:**
```json
{
  "status": "success",
  "client_id": "string",
  "total_stores": 0,
  "stores": [
    {
      "store_id": 0,
      "name": "string",
      "type": "string",
      "total_objects": 0,
      "objects": [],
      "objects_by_type": {},
      "object_type_counts": {}
    }
  ],
  "timestamp": "2025-08-03T10:30:00.000Z"
}
```

### Get Discovered Objects Summary
Get summary statistics of discovered objects for a client.

**Endpoint:** `GET /discovered-objects/{client_id}/summary`

**Parameters:**
- `client_id` (path): Client ID

**Response:**
```json
{
  "status": "success",
  "client_id": "string",
  "summary": {
    "total_objects": 0,
    "total_size_bytes": 0,
    "total_size_human": "0 B",
    "accessible_objects": 0,
    "inaccessible_objects": 0,
    "accessibility_rate": 0.0
  },
  "by_type": {
    "counts": {},
    "sizes": {},
    "sizes_human": {}
  },
  "by_store": {},
  "timestamp": "2025-08-03T10:30:00.000Z"
}
```

### Get Discovered Objects for Specific Store
Get discovered objects for a specific data store.

**Endpoint:** `GET /discovered-objects/{client_id}/store/{store_id}`

**Parameters:**
- `client_id` (path): Client ID
- `store_id` (path): Data store ID
- `limit` (query, optional): Maximum number of objects to return (default: 100)

**Response:**
```json
{
  "status": "success",
  "client_id": "string",
  "store": {
    "store_id": 0,
    "name": "string",
    "type": "string"
  },
  "total_objects": 0,
  "objects": [],
  "objects_by_type": {},
  "type_counts": {},
  "timestamp": "2025-08-03T10:30:00.000Z"
}
```

### Clear Discovered Objects for Store
Clear all discovered objects for a specific data store (useful for re-discovery).

**Endpoint:** `DELETE /discovered-objects/{client_id}/store/{store_id}`

**Parameters:**
- `client_id` (path): Client ID
- `store_id` (path): Data store ID

**Response:**
```json
{
  "status": "success",
  "message": "Cleared discovered objects for store {store_id}",
  "client_id": "string",
  "store_id": 0,
  "timestamp": "2025-08-03T10:30:00.000Z"
}
```

### Search Discovered Objects
Search discovered objects by name, path, or metadata.

**Endpoint:** `GET /discovered-objects/{client_id}/search`

**Parameters:**
- `client_id` (path): Client ID
- `query` (query): Search query (searches in name, path, metadata)
- `object_type` (query, optional): Filter by object type (file, table, etc.)
- `store_id` (query, optional): Filter by store ID
- `limit` (query, optional): Maximum number of results (default: 50)

**Response:**
```json
{
  "status": "success",
  "client_id": "string",
  "query": "string",
  "filters": {
    "object_type": "string",
    "store_id": 0
  },
  "total_matches": 0,
  "objects": [],
  "timestamp": "2025-08-03T10:30:00.000Z"
}
```

---

## Pipeline Orchestration

### Run Complete Pipeline
Run the complete data protection pipeline (Discovery → SDE → Scanning → Detection).

**Endpoint:** `POST /run-pipeline`

**Request Body:**
```json
{
  "client_id": "string"
}
```

**Response:**
```json
{
  "status": "success|failed",
  "message": "string",
  "discovery_results": {},
  "sde_results": [],
  "scan_results": {},
  "detection_results": [],
  "execution_timestamp": "2025-08-03T10:30:00.000Z",
  "errors": []
}
```

---

## Data Models

### ClientRequest
```json
{
  "client_id": "string"
}
```

### SpecificDatabaseScanRequest
```json
{
  "client_id": "string",
  "store_name": "string",
  "tables": ["string"] // optional
}
```

### SDESelectionRequest
```json
{
  "client_id": "string",
  "pattern_names": ["string"]
}
```

### Error Response
```json
{
  "detail": "string"
}
```

---

## Scanning Strategies

The API provides three distinct scanning strategies:

1. **Intelligent Selective (`/scan-latest`)**
   - ✅ If selected_objects exist → Use selective scanning
   - 🔄 If no selected_objects → Fall back to full latest database scan
   - 📊 Returns `selective_scan_used` flag

2. **Force Full Scan (`/scan-all`)**
   - 🚫 Always ignores selected_objects table
   - 🔄 Always performs full scan of all databases
   - 📊 `selective_scan_used` = false

3. **Force Selective Only (`/scan-selected-only`)**
   - ✅ Only scans if selected_objects exist
   - ❌ Fails with 400 error if no selections
   - 📊 Returns count of selected objects

---

## HTTP Status Codes

- `200 OK`: Successful operation
- `400 Bad Request`: Invalid request parameters or missing required selections
- `404 Not Found`: Resource not found (e.g., client_id, store_id)
- `500 Internal Server Error`: Server error during processing

---

## Rate Limiting & Best Practices

- **Bulk Operations**: Use `/discover-all-missing` for bulk discovery rather than individual calls
- **Pagination**: Use `limit` parameters for large datasets
- **Error Handling**: Always check the `status` field in responses
- **Selective Scanning**: Select appropriate scanning strategy based on use case
- **SDE Management**: Update SDE selections before running scans for better results

---

## Examples

### Complete Workflow Example

1. **Discovery**
```bash
curl -X POST "https://agents-1071432896229.asia-south2.run.app/discover" \
  -H "Content-Type: application/json" \
  -d '{"client_id": "your_client_id"}'
```

2. **Configure SDE Patterns**
```bash
curl -X POST "https://agents-1071432896229.asia-south2.run.app/client-sdes" \
  -H "Content-Type: application/json" \
  -d '{"client_id": "your_client_id", "pattern_names": ["email", "phone", "ssn"]}'
```

3. **Run Intelligent Scan**
```bash
curl -X POST "https://agents-1071432896229.asia-south2.run.app/scan-latest" \
  -H "Content-Type: application/json" \
  -d '{"client_id": "your_client_id"}'
```

4. **Check Results**
```bash
curl "https://agents-1071432896229.asia-south2.run.app/discovered-objects/your_client_id/summary"
```

---

*Last Updated: August 3, 2025*
