# Data Protection Backend API

A comprehensive data protection and scanning engine built with FastAPI that provides data discovery, scanning, detection, and risk assessment capabilities.

## Features

- **Multi-Connector Scanning**: Support for files, cloud storage (AWS S3, Google Cloud Storage, Azure Blob), and databases
- **Sensitive Data Detection**: Advanced pattern matching for PII, PHI, and other sensitive data
- **Risk Assessment**: AI-powered risk analysis and scoring
- **Report Generation**: Automated report generation in multiple formats
- **Modular Architecture**: Separate agents for discovery, scanning, detection, and risk assessment

## Quick Start

### Using Docker

1. **Build the Docker image:**
   ```bash
   docker build -t data-protection-backend .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8000:8000 data-protection-backend
   ```

3. **Access the API:**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirement.txt
   ```

2. **Set environment variables:**
   ```bash
   # Create .env file with your configuration
   DB_URL=your_database_url
   OPENROUTER_API_KEY=your_openrouter_api_key
   LLM_MODEL=mistralai/mistral-7b-instruct
   ```

3. **Run the application:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

## API Endpoints

### Main Scanning Engine (`/`)

#### Scan Operations
- **POST** `/scan` - Scan a data source (file/cloud)
  - Body: `ScanSourceConfig` (name, type, file_path, connection_string, etc.)
  - Returns: Scan ID and findings

- **POST** `/scan/upload` - Scan an uploaded file
  - Body: File upload with `perform_content_scan` parameter
  - Returns: Scan ID and findings

#### Results & Reports
- **GET** `/findings/{scan_id}` - Get findings for a specific scan
- **GET** `/report/{scan_id}` - Download scan report as JSON
- **GET** `/scans` - List all scan jobs
- **DELETE** `/scan/{scan_id}` - Delete a scan job and its report

#### Health & Status
- **GET** `/health` - Health check endpoint

### Risk Assessment API (`/risk/`)

#### Risk Assessment Operations
- **POST** `/risk/risk-assessment` - Perform risk assessment for a client
  - Body: `RiskAssessmentRequest` (client_id, risk_level, sensitivity, data_source)
  - Returns: Comprehensive risk assessment results

- **GET** `/risk/risk-assessments/{client_id}` - Get risk assessments for a client
  - Query params: `limit` (default: 10)
  - Returns: List of risk assessments

#### Metrics & Analytics
- **GET** `/risk/total-data-sources/{client_id}` - Get total data sources count
- **GET** `/risk/total-sdes/{client_id}` - Get total SDEs count
- **GET** `/risk/scanned-sdes/{client_id}` - Get scanned SDEs count
- **GET** `/risk/high-risk-sdes/{client_id}` - Get high-risk SDEs count
- **GET** `/risk/high-risk-records/{client_id}` - Get high-risk records count
- **GET** `/risk/total-sensitive-records/{client_id}` - Get total sensitive records
- **GET** `/risk/total-scans/{client_id}` - Get total scans count
- **GET** `/risk/risk-score/{client_id}` - Get risk score for client
- **GET** `/risk/confidence-score/{client_id}` - Get confidence score
- **GET** `/risk/last-scan-time/{client_id}` - Get last scan timestamp
- **GET** `/risk/next-scheduled-scan/{client_id}` - Get next scheduled scan
- **GET** `/risk/all-metrics/{client_id}` - Get all risk metrics for client

#### Data Analysis
- **GET** `/risk/dataset-names/{client_id}` - Get dataset names for client
- **GET** `/risk/data-sources/{client_id}` - Get data sources for client
- **GET** `/risk/filtered-findings/` - Get filtered findings
  - Query params: `client_id`, `data_source`, `risk_level`, `sensitivity`
- **GET** `/risk/scan-activity/{client_id}` - Get scan activity for client
- **GET** `/risk/sde-count/` - Get SDE count by pattern and data source
  - Query params: `pattern_name`, `data_source`

#### AI & Reports
- **GET** `/risk/llm-summary/{client_id}` - Get AI-generated risk summary
- **POST** `/risk/report` - Generate risk report
  - Body: `ReportRequest` (client_id, format, name, email, company)
  - Returns: Generated report file

#### System & Debug
- **GET** `/risk/db-status` - Check database connection status
- **GET** `/risk/debug-regex-patterns` - Debug regex patterns
- **POST** `/risk/cleanup` - Clean up old reports
- **GET** `/connections/exists/{client_id}` - Check if connections exist

### Pipeline API (`/`)

#### Pipeline Operations
- **POST** `/run-pipeline` - Run complete data protection pipeline
  - Body: `ClientRequest` (client_id)
  - Returns: `DriverResponse` with results from all agents

## Data Models

### ScanSourceConfig
```json
{
  "name": "string",
  "type": "string", // 'file', 'cloud', etc.
  "file_path": "string (optional)",
  "connection_string": "string (optional)",
  "perform_content_scan": "boolean (optional)",
  "baseline_config": "object (optional)"
}
```

### RiskAssessmentRequest
```json
{
  "client_id": "string",
  "risk_level": "array of integers (optional)", // 0=medium, 1=high, -1=low
  "sensitivity": "array of integers (optional)", // 0=medium, 1=high, -1=low
  "data_source": "array of integers (optional)" // List of store_ids
}
```

### ReportRequest
```json
{
  "client_id": "string",
  "format": "string", // 'pdf' or 'html'
  "name": "string (optional)",
  "email": "string (optional)",
  "company": "string (optional)"
}
```

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DB_URL` | PostgreSQL database connection string | Yes | - |
| `OPENROUTER_API_KEY` | OpenRouter API key for LLM features | Yes | - |
| `LLM_MODEL` | LLM model to use | No | `mistralai/mistral-7b-instruct` |

## Docker Commands

### Build and Run
```bash
# Build the image
docker build -t data-protection-backend .

# Run with environment variables
docker run -p 8000:8000 \
  -e DB_URL="your_db_url" \
  -e OPENROUTER_API_KEY="your_api_key" \
  data-protection-backend

# Run in detached mode
docker run -d -p 8000:8000 --name data-protection-app data-protection-backend
```

### Docker Desktop Monitoring

1. **Open Docker Desktop**
2. **Go to "Containers" tab**
3. **Find your container** (named `data-protection-app` if you used the --name flag)
4. **Click on the container** to see:
   - **Logs**: Real-time application logs
   - **Stats**: CPU, memory, and network usage
   - **Files**: Container file system
   - **Terminal**: Interactive shell access

### Container Management
```bash
# View running containers
docker ps

# View container logs
docker logs data-protection-app

# Stop the container
docker stop data-protection-app

# Remove the container
docker rm data-protection-app

# View container stats
docker stats data-protection-app
```

## Health Check

The application includes a health check endpoint at `/health` that returns:
```json
{
  "status": "ok"
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error

## Development

### Project Structure
```
backend/
├── agents/                 # Modular agents
│   ├── modular_discovery_agent.py
│   ├── modular_scanning_agent.py
│   ├── modular_detection_agent.py
│   ├── modular_risk_assessment_agent.py
│   └── driver.py
├── scanning_engine/        # Core scanning functionality
│   ├── scanner.py
│   ├── baseline_manager.py
│   └── scanners/
├── main.py                # Main FastAPI application
├── requirement.txt        # Python dependencies
├── Dockerfile            # Docker configuration
└── README.md             # This file
```

### Adding New Endpoints

1. Add the endpoint to the appropriate agent file
2. Update this README with the new endpoint documentation
3. Test the endpoint using the interactive API docs at `/docs`

## Support

For issues and questions:
1. Check the application logs
2. Verify environment variables are set correctly
3. Ensure database connectivity
4. Review the API documentation at `/docs` 