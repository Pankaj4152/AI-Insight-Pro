# Connectors API

A modular FastAPI application for managing database connections and model inventory.

## Project Structure

```
connectors/
├── app/
│   ├── __init__.py
│   ├── main.py              #FastAPI app creation and configuration
│   ├── config.py            # Configuration settings
│   ├── models.py            # Pydantic models
│   ├── database.py          # Database operations
│   ├── utils.py             # Utility functions
│   └── routers/
│       ├── __init__.py
│       ├── validation.py    # Connection validation endpoints
│       ├── model_inventory.py  # Model inventory endpoints
│       └── general.py       # General endpoints
├── credentials/             # Local credentials storage (gitignored)
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Features

- **Database Connection Validation**: Support for MySQL, PostgreSQL, BigQuery, and GCP Bucket
- **Model Inventory Management**: Add, list, and delete model entries
- **Connection History**: Track connection attempts and status
- **SDE Catalogue**: Manage Sensitive Data Elements by industry
- **Modular Architecture**: Clean separation of concerns with routers, models, and utilities
- **Docker Support**: Easy containerization and deployment


## API Endpoints

### Validation
- `POST /validate/mysql` - Validate MySQL credentials
- `POST /validate/postgresql` - Validate PostgreSQL credentials
- `POST /validate/bigquery` - Validate BigQuery credentials
- `POST /validate/gcp-bucket` - Validate GCP bucket credentials
- `POST /validate/gcp-bucket-json` - Validate GCP bucket with JSON payload

### Model Inventory
- `POST /model-inventory/add` - Add a new model
- `GET /model-inventory/list` - List models for a client
- `DELETE /model-inventory/delete/{model_id}` - Delete a model

### General
- `GET /connection-history/{client_id}` - Get connection history
- `GET /industry-classifications` - Get industry classifications
- `GET /get-sde` - Get SDEs by industry
- `POST /add-sde` - Add new SDE

### Utility
- `GET /` - Root endpoint
- `GET /health` - Health check

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DB_URL` | PostgreSQL connection string | Yes |
| `GCP_BUCKET_NAME` | GCP bucket name for credential storage | Yes |
| `GCP_PROJECT_ID` | GCP project ID | Yes |
| `CLOUD_RUN_SERVICE_URL` | Cloud Run service URL | No |

## Development

### Adding New Endpoints

1. Create or modify routers in `app/routers/`
2. Add models to `app/models.py` if needed
3. Add database functions to `app/database.py` if needed
4. Include the router in `app/main.py`

### Database Operations

All database operations are centralized in `app/database.py`. This includes:
- Connection management
- CRUD operations
- History tracking

### Testing

Test the API using the interactive documentation at http://localhost:8000/docs

## Docker Commands

```bash
# Build the image
docker build -t connectors-api .

# Run the container
docker run -p 8000:8000 --env-file .env connectors-api


## Security Notes

- Credentials are temporarily stored locally and then uploaded to GCS
- Local credential files are automatically cleaned up after upload
- Connection attempts are logged for audit purposes
- Sensitive information should be stored in environment variables
