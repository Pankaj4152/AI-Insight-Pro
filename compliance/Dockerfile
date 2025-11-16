# Use lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (for psycopg2/PostgreSQL support)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app files
COPY . .

# Install dotenv loader
RUN pip install python-dotenv gunicorn

# Environment variable for Cloud Run
ENV PORT=5000
EXPOSE 5000

# Start Flask using Gunicorn for better performance
CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 0 api:app
