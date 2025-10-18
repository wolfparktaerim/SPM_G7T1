# backend/task-service/Dockerfile

# Use an official Python runtime as base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY shared /app/shared     
COPY comment-service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY comment-service/ .

# Copy the application code
COPY . .

# Expose port 5000 for Flask
EXPOSE 6006

# Run the app
CMD ["python", "app.py"]
