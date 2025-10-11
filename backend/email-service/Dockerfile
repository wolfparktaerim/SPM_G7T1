# backend/email-service/Dockerfile

# Use official Python runtime as base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY shared /app/shared     

COPY email-service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY email-service/ .

# Copy application code
COPY . .

# Expose port
EXPOSE 6005

# Run the application
CMD ["python", "app.py"]
