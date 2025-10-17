# backend/notification-service/Dockerfile

# Use an official Python runtime as base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY shared /app/shared     
COPY notification-service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY notification-service/ .

# Copy the application code
COPY . .

# Expose port 6004 for Flask
EXPOSE 6004

# Run the app
CMD ["python", "app.py"]
