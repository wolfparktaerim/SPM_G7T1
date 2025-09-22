# subtask-service/Dockerfile

# Use an official Python runtime as base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose port 6003 for Flask
EXPOSE 6003

# Run the app
CMD ["python", "app.py"]