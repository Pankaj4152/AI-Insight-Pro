# Use a lightweight official Python image as the base
FROM python:3.10-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container
COPY . .

# Expose the port the FastAPI application will run on
EXPOSE 8080
# Command to run the application using Uvicorn
# You might want to adjust --host and --port based on your deployment needs.
# For production, consider using gunicorn with uvicorn workers for better performance and reliability.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]