# SDE Catalogue API Documentation

## Overview
The SDE Catalogue API provides endpoints for managing Sensitive Data Entities (SDEs) selection and configuration for clients. This API enables clients to view their registered industry, browse available SDE patterns, and save their selected SDEs for Risk assessment.

## Base URL
```
http://localhost:8080/catalogue
```

## Authentication
Currently, the API does not require authentication. In production, implement proper authentication mechanisms.

## Database Requirements

### Required Tables

1. **client_prof** - Client profile table
   ```sql
   CREATE TABLE client_prof (
       client_id VARCHAR(255) PRIMARY KEY,
       industry VARCHAR(100),
       -- other client fields
   );
   ```

2. **sde_patterns** - SDE patterns table
   ```sql
   CREATE TABLE sde_patterns (
       pattern_name VARCHAR(255) PRIMARY KEY,
       sensitivity VARCHAR(50),
       protection_method VARCHAR(255),
       industry VARCHAR(100) DEFAULT 'all-purpose'
   );
   ```

3. **client_selected_sdes** - Client SDE selections table (auto-created)
   ```sql
   CREATE TABLE client_selected_sdes (
       id SERIAL PRIMARY KEY,
       client_id VARCHAR(255) NOT NULL,
       pattern_name VARCHAR(255) NOT NULL,
       sensitivity VARCHAR(50),
       protection_method VARCHAR(255),
       selected_at TIMESTAMP DEFAULT NOW(),
       UNIQUE(client_id, pattern_name)
   );
   ```

## Endpoints

### 1. Get Available Industries
**GET** `/catalogue/industries/available`

Get all available industries for filtering SDEs.

**Response:**
```json
{
  "status": "success",
  "count": 6,
  "industries": [
    "Education",
    "Finance",
    "Healthcare",
    "Manufacturing",
    "Retail",
    "Technology"
  ]
}
```

---

### 2. Get Client Industry
**GET** `/catalogue/client/{client_id}/industry`

Get the registered industry for a specific client.

**Parameters:**
- `client_id` (string): The client ID

**Response:**
```json
{
  "status": "success",
  "client_id": "client_123",
  "industry": "Finance"
}
```

**Error Response (404):**
```json
{
  "detail": "Client client_123 not found or no industry registered"
}
```

---

### 3. Get Available SDEs
**GET** `/catalogue/sdes/available`

Get all available SDE patterns, optionally filtered by industry.

**Query Parameters:**
- `industry_filter` (string, optional): Filter SDEs by industry

**Response:**
```json
{
  "status": "success",
  "count": 15,
  "sdes": [
    {
      "pattern_name": "email",
      "sensitivity": "high",
      "protection_method": "encryption",
      "industry": "all-purpose"
    },
    {
      "pattern_name": "credit_card",
      "sensitivity": "high",
      "protection_method": "tokenization",
      "industry": "Finance"
    }
  ],
  "industry_filter": "Finance"
}
```

---

### 4. Save Client Selected SDEs
**POST** `/catalogue/sdes/save-selected`

Save the SDEs selected by a client.

**Request Body:**
```json
{
  "client_id": "client_123",
  "selected_sdes": [
    {
      "pattern_name": "email",
      "sensitivity": "high",
      "protection_method": "encryption"
    },
    {
      "pattern_name": "phone_number",
      "sensitivity": "medium",
      "protection_method": "masking"
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully saved 2 selected SDEs for client client_123",
  "client_id": "client_123",
  "saved_count": 2
}
```

---

### 5. Get Client Selected SDEs
**GET** `/catalogue/client/{client_id}/selected-sdes`

Get the SDEs that a client has selected.

**Parameters:**
- `client_id` (string): The client ID

**Response:**
```json
{
  "status": "success",
  "client_id": "client_123",
  "count": 2,
  "selected_sdes": [
    {
      "pattern_name": "email",
      "sensitivity": "high",
      "protection_method": "encryption",
      "selected_at": "2024-01-15T10:30:00Z"
    },
    {
      "pattern_name": "phone_number",
      "sensitivity": "medium",
      "protection_method": "masking",
      "selected_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### 6. Get Complete SDE Catalogue
**GET** `/catalogue/catalogue/{client_id}`

Get complete SDE catalogue information for a client including their industry, available SDEs, and previously selected SDEs.

**Parameters:**
- `client_id` (string): The client ID

**Query Parameters:**
- `industry_filter` (string, optional): Filter available SDEs by industry

**Response:**
```json
{
  "status": "success",
  "client_id": "client_123",
  "registered_industry": "Finance",
  "available_sdes": {
    "count": 15,
    "sdes": [...]
  },
  "selected_sdes": {
    "count": 2,
    "sdes": [...]
  },
  "industry_filter": "Finance"
}
```

## Usage Examples

### Frontend Integration

```javascript
// Get client's industry
const getClientIndustry = async (clientId) => {
  const response = await fetch(`/catalogue/client/${clientId}/industry`);
  const data = await response.json();
  return data.industry;
};

// Get available SDEs for client's industry
const getAvailableSDEs = async (industry) => {
  const response = await fetch(`/catalogue/sdes/available?industry_filter=${industry}`);
  const data = await response.json();
  return data.sdes;
};

// Save client's SDE selections
const saveSelectedSDEs = async (clientId, selectedSDEs) => {
  const response = await fetch('/catalogue/sdes/save-selected', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      client_id: clientId,
      selected_sdes: selectedSDEs
    })
  });
  return response.json();
};
```

### Python Integration

```python
import requests

# Get complete catalogue for a client
def get_sde_catalogue(client_id):
    response = requests.get(f"http://localhost:8080/catalogue/catalogue/{client_id}")
    return response.json()

# Save selected SDEs
def save_sde_selections(client_id, selected_sdes):
    payload = {
        "client_id": client_id,
        "selected_sdes": selected_sdes
    }
    response = requests.post(
        "http://localhost:8080/catalogue/sdes/save-selected",
        json=payload
    )
    return response.json()
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- **200**: Success
- **400**: Bad Request (invalid input)
- **404**: Not Found (client not found)
- **500**: Internal Server Error

Error responses include a `detail` field with the error message:

```json
{
  "detail": "Error message here"
}
```

## Testing

Use the provided test script to verify the API functionality:

```bash
python test_sde_catalogue.py
```

## Notes

1. The `client_selected_sdes` table is automatically created if it doesn't exist.
2. If the `industry` column doesn't exist in the `sde_patterns` table, all SDEs are treated as "all-purpose".
3. Client selections are unique per client and pattern (duplicate selections are replaced).
4. The API supports both industry-specific and all-purpose SDE patterns. 