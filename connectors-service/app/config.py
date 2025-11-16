import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DB_URL = os.getenv("DB_URL")

# GCP Configuration
GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")

# Cloud Run Configuration
CLOUD_RUN_SERVICE_URL = os.getenv("CLOUD_RUN_SERVICE_URL", "https://risk-analyzer-1071432896229.asia-south2.run.app")

# CORS Configuration
CORS_ORIGINS = ["*"]
CORS_CREDENTIALS = True
CORS_METHODS = ["*"]
CORS_HEADERS = ["*"]
