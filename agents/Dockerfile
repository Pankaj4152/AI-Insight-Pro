# Use Python 3.11 slim image as base
FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies
# These are necessary for compiling certain Python packages with C extensions
# Added 'ca-certificates' to resolve SSL/TLS issues during apk update/add.
RUN apk update --no-cache && apk add --no-cache \
    ca-certificates \
    gcc \
    g++ \
    postgresql-dev \
    curl \
    musl-dev \
    linux-headers \
    # Add libffi-dev for packages like cryptography, if needed
    libffi-dev

# Copy requirements file first for better caching.
# Assuming your requirements file is named 'requirements.txt' (plural).
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir reduces the image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
# Ensure you have a .dockerignore file to exclude unnecessary files (e.g., .git, __pycache__, .env)
COPY . .

# Create necessary directories.
# Note: For persistent data, consider using Docker volumes instead of creating
# these directories directly in the image, as data inside the image is ephemeral.
RUN mkdir -p /app/logs /app/temp /app/reports

# Expose port
EXPOSE 8080

# Health check to ensure the application is running
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Copy startup script
COPY startup_debug.py .

# Run the application
# Use startup script that handles PORT environment variable properly
CMD ["python", "startup_debug.py"]
