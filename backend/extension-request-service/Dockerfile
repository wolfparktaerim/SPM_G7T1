# backend/extension-request-service/Dockerfile

# Use an official Python runtime as base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY shared /app/shared     
COPY extension-request-service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY extension-request-service/ .

# Copy the application code
COPY . .

# Expose port 6007 for Flask
EXPOSE 6007

# Run the app
CMD ["python", "app.py"]
