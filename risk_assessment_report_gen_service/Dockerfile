# Risk Assessment Application Dockerfile
# Production version for Google Cloud deployment

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app:$PYTHONPATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser

# Create application directory and set ownership
WORKDIR /app
RUN chown -R appuser:appuser /app

# Copy requirements and install Python dependencies
COPY requirement.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirement.txt

# Switch to non-root user
USER appuser

# Create necessary directories (no reports dir - using temp files)
RUN mkdir -p /app/logs

# Copy only essential production files
COPY --chown=appuser:appuser risk.py /app/
COPY --chown=appuser:appuser modular_report_generation_agent.py /app/
COPY --chown=appuser:appuser config_manager.py /app/
COPY --chown=appuser:appuser postgresql_db_manager.py /app/
COPY --chown=appuser:appuser llm_client.py /app/
COPY --chown=appuser:appuser agent_config.yaml /app/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
# Expose the port the app runs on
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/risk/db-status || exit 1

# Default command to run the application
CMD ["uvicorn", "risk:app", "--host", "0.0.0.0", "--port", "8000"]
