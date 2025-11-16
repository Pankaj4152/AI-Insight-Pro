# 🚀 Data Privacy Scanning API Documentation

## Overview
This API provides comprehensive data privacy scanning capabilities with SDE (Sensitive Data Element) based filtering. The system supports scanning multiple data source types including GCS buckets, BigQuery datasets, PostgreSQL databases, MySQL databases, and file systems.

## 🏗️ System Architecture

### Key Features
- **SDE-Based Filtering**: Clients can select specific sensitive data types to scan for
- **Multi-Source Support**: GCS, BigQuery, PostgreSQL, MySQL, Files
- **Multi-Tenant**: Each client has isolated data and configurations
- **Backward Compatibility**: Clients without SDE selections use all patterns
- **Real-time Scanning**: On-demand scanning with immediate results

### Database Schema
```
📊 Core Tables:
├── client_prof - Client profile information
├── sde_patterns - Available SDE pattern definitions
├── client_selected_sdes - Client SDE selections (NEW)
├── data_stores - Client data sources
├── scans - Scan execution records
└── scan_findings - Detected sensitive data findings
```

## 🌐 API Endpoints

### Base URL
```
http://localhost:8000
```

---

## 🔍 **Scanning Endpoints**

### 1. Scan Latest Database
Scan only the most recently discovered database for a client.

**Endpoint:** `POST /scan-latest`

**Request Body:**
```json
{
  "client_id": "9LYPHynJIjR8c"
}
```

**Response:**
```json
{
  "status": "success",
  "client_id": "9LYPHynJIjR8c",
  "scan_type": "latest_database",
  "results": {
    "total_sources_scanned": 1,
    "total_findings": 15,
    "scan_duration": "45.2s",
    "findings_by_type": {
      "email_address": 8,
      "phone_number": 4,
      "credit_card_number": 3
    },
    "detailed_results": [
      {
        "source_name": "customer-data-bucket",
        "source_type": "gcs",
        "findings": 15,
        "status": "completed"
      }
    ]
  },
  "timestamp": "2025-08-03T10:30:45.123Z"
}
```

---

### 2. Scan All Databases
Scan all discovered databases for a client.

**Endpoint:** `POST /scan-all`

**Request Body:**
```json
{
  "client_id": "9LYPHynJIjR8c"
}
```

**Response:**
```json
{
  "status": "success",
  "client_id": "9LYPHynJIjR8c",
  "scan_type": "all_databases",
  "results": {
    "total_sources_scanned": 5,
    "total_findings": 47,
    "scan_duration": "2m 15s",
    "findings_by_type": {
      "email_address": 20,
      "phone_number": 15,
      "credit_card_number": 8,
      "person_name": 4
    },
    "detailed_results": [
      {
        "source_name": "customer-data-bucket",
        "source_type": "gcs",
        "findings": 15,
        "status": "completed"
      },
      {
        "source_name": "analytics_dataset",
        "source_type": "bigquery",
        "findings": 22,
        "status": "completed"
      },
      {
        "source_name": "user_profiles",
        "source_type": "postgresql",
        "findings": 10,
        "status": "completed"
      }
    ]
  },
  "timestamp": "2025-08-03T10:35:22.456Z"
}
```

---

### 3. Scan Specific Database/Resource
Scan a specific database, bucket, or dataset.

**Endpoint:** `POST /scan-specific`

**Request Body:**
```json
{
  "client_id": "9LYPHynJIjR8c",
  "store_name": "customer-data-bucket",
  "tables": ["users", "orders"]  // Optional: specific tables to scan
}
```

**Response:**
```json
{
  "status": "success",
  "client_id": "9LYPHynJIjR8c",
  "scan_type": "specific_database",
  "store_name": "customer-data-bucket",
  "results": {
    "source_name": "customer-data-bucket",
    "source_type": "gcs",
    "total_findings": 15,
    "scan_duration": "32.1s",
    "tables_scanned": ["users", "orders"],
    "findings": [
      {
        "sde_type": "email_address",
        "field_name": "email",
        "data_value": "user@example.com",
        "sensitivity": "high",
        "confidence_score": 0.95,
        "location_metadata": {
          "file_path": "gs://customer-data-bucket/users.json",
          "line_number": 42
        }
      }
    ]
  },
  "timestamp": "2025-08-03T10:40:11.789Z"
}
```

---

## 🎯 **SDE Management Endpoints**

### 4. Get Available SDEs
Retrieve all available Sensitive Data Element types that clients can select.

**Endpoint:** `GET /available-sdes`

**Response:**
```json
{
  "available_sdes": [
    {
      "pattern_name": "email_address",
      "description": "Pattern for detecting email addresses"
    },
    {
      "pattern_name": "phone_number", 
      "description": "Pattern for detecting phone numbers"
    },
    {
      "pattern_name": "credit_card_number",
      "description": "Pattern for detecting credit card numbers"
    },
    {
      "pattern_name": "aadhaar_number",
      "description": "Pattern for detecting Aadhaar numbers"
    },
    {
      "pattern_name": "pan_number",
      "description": "Pattern for detecting PAN numbers"
    }
  ],
  "total_count": 25,
  "timestamp": "2025-08-03T10:45:33.123Z"
}
```

---

### 5. Get Client SDE Selections
View current SDE selections for a specific client.

**Endpoint:** `GET /client-sdes/{client_id}`

**Example:** `GET /client-sdes/9LYPHynJIjR8c`

**Response:**
```json
{
  "client_id": "9LYPHynJIjR8c",
  "selected_sdes": [
    {
      "pattern_name": "email_address",
      "sensitivity": "high",
      "protection_method": "encryption",
      "selected_at": "2025-08-03T09:15:22.456Z"
    },
    {
      "pattern_name": "phone_number",
      "sensitivity": "medium",
      "protection_method": "masking",
      "selected_at": "2025-08-03T09:15:22.456Z"
    },
    {
      "pattern_name": "credit_card_number",
      "sensitivity": "high",
      "protection_method": "encryption",
      "selected_at": "2025-08-03T09:15:22.456Z"
    }
  ],
  "total_count": 3,
  "timestamp": "2025-08-03T10:50:15.789Z"
}
```

---

### 6. Update Client SDE Selections
Update the SDE selections for a client. This replaces all existing selections.

**Endpoint:** `POST /client-sdes`

**Request Body:**
```json
{
  "client_id": "9LYPHynJIjR8c",
  "pattern_names": [
    "email_address",
    "phone_number",
    "credit_card_number",
    "person_name"
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "client_id": "9LYPHynJIjR8c",
  "selected_sdes": [
    {
      "pattern_name": "email_address",
      "sensitivity": "medium",
      "protection_method": "encryption",
      "selected_at": "2025-08-03T10:55:30.123Z"
    },
    {
      "pattern_name": "phone_number",
      "sensitivity": "medium", 
      "protection_method": "encryption",
      "selected_at": "2025-08-03T10:55:30.123Z"
    },
    {
      "pattern_name": "credit_card_number",
      "sensitivity": "medium",
      "protection_method": "encryption", 
      "selected_at": "2025-08-03T10:55:30.123Z"
    },
    {
      "pattern_name": "person_name",
      "sensitivity": "medium",
      "protection_method": "encryption",
      "selected_at": "2025-08-03T10:55:30.123Z"
    }
  ],
  "total_count": 4,
  "message": "Updated SDE selections for client 9LYPHynJIjR8c",
  "timestamp": "2025-08-03T10:55:30.123Z"
}
```

---

## 🔧 **Management Endpoints**

### 7. Data Discovery
Discover new data sources for a client.

**Endpoint:** `POST /discover`

**Request Body:**
```json
{
  "client_id": "9LYPHynJIjR8c"
}
```

**Response:**
```json
{
  "status": "success",
  "client_id": "9LYPHynJIjR8c",
  "results": {
    "total_sources_discovered": 8,
    "new_sources": 3,
    "source_types": {
      "gcs": 3,
      "bigquery": 2,
      "postgresql": 2,
      "mysql": 1
    },
    "sources": [
      {
        "name": "customer-data-bucket",
        "type": "gcs",
        "location": "api-gateway-463207",
        "discovered_at": "2025-08-03T11:00:15.456Z"
      }
    ]
  },
  "timestamp": "2025-08-03T11:00:15.456Z"
}
```

---

### 8. List Client Databases
Get all databases/sources for a client.

**Endpoint:** `GET /list-databases/{client_id}`

**Example:** `GET /list-databases/9LYPHynJIjR8c`

**Response:**
```json
{
  "client_id": "9LYPHynJIjR8c",
  "databases": [
    {
      "store_id": 15,
      "store_name": "customer-data-bucket",
      "store_type": "gcs_bucket",
      "location": "api-gateway-463207",
      "discovery_timestamp": "2025-08-03T09:30:22.123Z"
    },
    {
      "store_id": 16,
      "store_name": "analytics_dataset", 
      "store_type": "bigquery",
      "location": "api-gateway-463207",
      "discovery_timestamp": "2025-08-03T09:31:15.456Z"
    }
  ],
  "total_count": 8,
  "timestamp": "2025-08-03T11:05:42.789Z"
}
```

---

### 9. Run Complete Pipeline
Execute the full data protection pipeline (Discovery → SDE → Scanning → Detection).

**Endpoint:** `POST /run-pipeline`

**Request Body:**
```json
{
  "client_id": "9LYPHynJIjR8c"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Pipeline execution completed successfully",
  "discovery_results": {
    "sources_discovered": 8,
    "new_sources": 2
  },
  "sde_results": [
    {
      "sde_type": "email_address",
      "patterns_loaded": 1
    }
  ],
  "scan_results": {
    "total_findings": 47,
    "sources_scanned": 8
  },
  "detection_results": [
    {
      "risk_level": "high",
      "findings_count": 15
    }
  ],
  "execution_timestamp": "2025-08-03T11:10:30.123Z",
  "errors": []
}
```

---

### 10. Health Check
Check API server health status.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-03T11:15:45.456Z"
}
```

---

## 📊 **Available SDE Types**

The system supports 25+ SDE types:

### Identity & Government
- `aadhaar_number` - Aadhaar identification numbers
- `pan_number` - PAN card numbers
- `indian_passport_number` - Indian passport numbers
- `indian_driving_license` - Driving license numbers
- `indian_voter_id` - Voter ID numbers

### Financial
- `credit_card_number` - Credit card numbers
- `indian_bank_account_number` - Bank account numbers
- `indian_ifsc_code` - IFSC codes
- `upi_id` - UPI payment IDs
- `currency_amount` - Currency amounts

### Personal Information
- `person_name` - Person names
- `email_address` - Email addresses
- `phone_number` - Phone numbers
- `date_of_birth` - Date of birth
- `address` - Physical addresses

### Location & Technical
- `ip_address` - IP addresses
- `url` - URLs and web links
- `latitude_longitude` - GPS coordinates
- `zip_postal_code_indian` - Postal codes
- `pincode` - PIN codes

### Data & Content
- `json_key_value` - JSON key-value pairs
- `html_tag` - HTML tags
- `hashtag` - Social media hashtags
- `mention` - Social media mentions
- `vehicle_registration_indian` - Vehicle registration numbers

## 🚦 **Error Handling**

### Common Error Responses

**400 Bad Request:**
```json
{
  "detail": "store_name must be provided"
}
```

**404 Not Found:**
```json
{
  "detail": "Source 'invalid-source' not found in any available sources"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Latest database scan failed: Database connection timeout"
}
```

## 🔐 **Authentication**
Currently, the API uses client_id based authentication. Each request must include a valid client_id that exists in the client_prof table.

## 📈 **Usage Examples**

### Complete Workflow Example

1. **Set up SDE preferences:**
```bash
curl -X POST "http://localhost:8000/client-sdes" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "9LYPHynJIjR8c",
    "pattern_names": ["email_address", "phone_number", "credit_card_number"]
  }'
```

2. **Discover data sources:**
```bash
curl -X POST "http://localhost:8000/discover" \
  -H "Content-Type: application/json" \
  -d '{"client_id": "9LYPHynJIjR8c"}'
```

3. **Scan latest database with SDE filtering:**
```bash
curl -X POST "http://localhost:8000/scan-latest" \
  -H "Content-Type: application/json" \
  -d '{"client_id": "9LYPHynJIjR8c"}'
```

4. **Check results:**
```bash
curl -X GET "http://localhost:8000/client-sdes/9LYPHynJIjR8c"
```

## 🎯 **Key Benefits**

- ✅ **Targeted Scanning**: Only scan for relevant SDE types
- ✅ **Performance**: 60-90% reduction in pattern processing
- ✅ **Compliance**: Align with specific regulatory requirements
- ✅ **Cost Efficiency**: Reduced compute time and resources
- ✅ **Client Control**: Flexible SDE selection management
- ✅ **Backward Compatibility**: Works with existing clients

## 🔧 **Development & Testing**

### Start the API Server
```bash
cd agents
python driver.py
```

### Test SDE Management
```bash
python test_sde_api.py
```

### View System Demo
```bash
python demo_sde_system.py
```

---

**API Version:** 1.0  
**Last Updated:** August 3, 2025  
**Support:** Team-A Development Team
