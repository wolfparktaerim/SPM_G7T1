# Task Management System

A microservices-based task management application with a Vue.js frontend and Flask backend services, using Firebase for authentication and data storage.

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Firebase Configuration](#2-firebase-configuration)
  - [3. Backend Environment Setup](#3-backend-environment-setup)
  - [4. Frontend Environment Setup](#4-frontend-environment-setup)
  - [5. Running with Docker](#5-running-with-docker)
- [Service Endpoints](#service-endpoints)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributors](#contributors)

---

## 🏗️ Architecture Overview

The application follows a microservices architecture:

- **Frontend**: Vue 3 + Vite (Port: 5173)
- **API Gateway**: Kong (Port: 8000)
- **Backend Services**:
  - Project Service (Port: 6001)
  - Task Service (Port: 6002)
  - Subtask Service (Port: 6003)
  - Notification Service (Port: 6004)
  - Email Service (Port: 6005)
  - Comment Service (Port: 6006)
  - Extension Request Service (Port: 6007)
- **Database**: Firebase Realtime Database
- **Authentication**: Firebase Authentication

---

## ✅ Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** & **Docker Compose**
- **Node.js** & **npm**
- **Python**
- **Firebase Account** (credential will be provided in the submission folder)
- **Git**

---

## 📁 Project Structure

```
.
├── backend/
│   ├── project-service/
│   ├── task-service/
│   ├── subtask-service/
│   ├── notification-service/
│   ├── email-service/
│   ├── comment-service/
│   ├── extension-request-service/
│   ├── compose.yaml           # Docker Compose configuration
│   ├── kong.yml.template      # Kong API Gateway template
│   ├── firebase-cred.json     # Firebase credentials (provided in the submission folder)
│   └── .env                   # Backend environment variables (provided in the submission folder)
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── .env                   # Frontend environment variables (provided in the submission folder)
└── README.md
```

---

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/wolfparktaerim/SPM_G7T1.git
cd SPM_G7T1
```

### 2. Firebase Configuration

Find the **firebase-cred.json** file in the submission folder (under subfolder #8).

Copy this file to the `backend/` directory:

```bash
# Place the firebase-cred.json in:
backend/firebase-cred.json
```

### 3. Backend Environment Setup

Create a `.env` file under the `/backend` folder:

```bash
cd backend
touch .env
```

Find the **backend_env.txt** file in the submission folder (under subfolder #8), copy the content and paste into the `.env` file.

### 4. Frontend Environment Setup

Create a `.env` file under the `/frontend` folder:

```bash
cd frontend
touch .env
```

Find the **frontend_env.txt** file in the submission folder (under subfolder #8), copy the content and paste into the `.env` file.

### 5. Running with Docker

Docker Compose will handle all backend services, Kong API Gateway, and their dependencies. **Ensure Docker Desktop is running.**

#### 5.1 Start All Services

```bash
cd backend
docker-compose up -d
```

This will start:

- All 7 backend microservices
- Kong API Gateway
- Kong configuration generator

#### 5.2 Verify Services are Running

```bash
docker-compose ps
```

You should see all services with status "Up".

#### 5.3 View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f project-service
```

#### 5.4 Start Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at **http://localhost:5173**

#### 5.5 Stop Services

```bash
cd backend
docker-compose down
```

To also remove volumes:

```bash
docker-compose down -v
```

---

## 🌐 Service Endpoints

### API Gateway (Kong)

- **Base URL**: `http://localhost:8000`
- **Admin API**: `http://localhost:8001`

### Individual Services (Direct Access)

- **Project Service**: `http://localhost:6001/project`
- **Task Service**: `http://localhost:6002/task`
- **Subtask Service**: `http://localhost:6003/subtask`
- **Notification Service**: `http://localhost:6004/notifications`
- **Email Service**: `http://localhost:6005/email`
- **Comment Service**: `http://localhost:6006/comments`
- **Extension Request Service**: `http://localhost:6007/extension-requests`

### Frontend

- **Development Server**: `http://localhost:5173`

---

## 🧪 Testing

### Backend Testing

#### Run All Tests with Docker

```bash
cd backend
python run_all_tests.py
```

#### Run Individual Service Tests

```bash
# Inside Docker container
docker exec backend-project-service-1 pytest test_project.py -v

# Or directly if running without Docker
cd backend/project-service
pytest test_project.py -v
```

### Frontend Testing

```bash
cd frontend

# Unit tests
npm run test:unit

# End-to-end tests
npm run test:e2e

# Linting
npm run lint
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. **Firebase Authentication Errors**

**Problem**: "Permission denied" or authentication failures

**Solution**:

- Verify `firebase-cred.json` is in the correct location (`backend/`)
- Check that `DATABASE_URL` in `.env` matches your Firebase project
- Ensure Firebase Realtime Database rules allow read/write access during development

#### 2. **Docker Services Not Starting**

**Problem**: Services fail to start or immediately exit

**Solution**:

```bash
# Check logs for specific service
docker-compose logs <service-name>

# Verify environment variables are set
docker-compose config

# Rebuild images
docker-compose up --build
```

#### 3. **Frontend Can't Connect to Backend**

**Problem**: API requests fail with CORS or connection errors

**Solution**:

- Verify Kong is running: `curl http://localhost:8000`
- Check `VITE_API_BASE_URL` in `frontend/.env` is set to `http://localhost:8000`
- Ensure all backend services are running: `docker-compose ps`

#### 4. **Email Notifications Not Sending**

**Problem**: Notification service fails to send emails

**Solution**:

- For Gmail: Generate an [App Password](https://support.google.com/accounts/answer/185833)
- Verify SMTP credentials in `backend/.env`
- Check email service logs: `docker-compose logs email-service`

#### 5. **Port Already in Use**

**Problem**: "Address already in use" error

**Solution**:

```bash
# Find process using the port (e.g., 6001)
lsof -i :6001

# Kill the process
kill -9 <PID>

# Or change the port in compose.yaml
```

#### 6. **Missing Firebase Credentials**

**Problem**: Services fail with "Could not load Firebase credentials"

**Solution**:

- Ensure `firebase-cred.json` exists in `backend/` directory
- Verify file permissions: `chmod 644 backend/firebase-cred.json`
- Check that the file is properly mounted in Docker volumes

#### 7. **Kong Configuration Issues**

**Problem**: Kong fails to start or routes don't work

**Solution**:

```bash
# Regenerate Kong configuration
docker-compose up kong-config-generator

# Check Kong configuration
cat backend/kong/config/kong.yml

# Restart Kong
docker-compose restart kong
```

## 👥 Contributors

This project was developed by **SPM Group 7 Team 1**:

<table>
  <tr>
    <th>Name</th>
    <th>Email</th>
  </tr>
  <tr>
    <td>Piao TaiLin</td>
    <td><a href="tailin.piao.2023@scis.smu.edu.sg">tailin.piao.2023@scis.smu.edu.sg</a></td>
  </tr>
  <tr>
    <td>Shamel</td>
    <td><a href="shamelt.2023@scis.smu.edu.sg">shamelt.2023@scis.smu.edu.sg</a></td>
  </tr>
  <tr>
    <td>Kyle</td>
    <td><a href="kyle.liow.2023@scis.smu.edu.sg">kyle.liow.2023@scis.smu.edu.sg</a></td>
  </tr>
  <tr>
    <td>Yiluan</td>
    <td><a href="yiluan.wen.2023@scis.smu.edu.sg">yiluan.wen.2023@scis.smu.edu.sg</a></td>
  </tr>
  <tr>
    <td>Jordan</td>
    <td><a href="jordanlim.2023@scis.smu.edu.sg">jordanlim.2023@scis.smu.edu.sg</a></td>
  </tr>
  <tr>
    <td>Isabel</td>
    <td><a href="isabel.lee.2023@scis.smu.edu.sg">isabel.lee.2023@scis.smu.edu.sg</a></td>
  </tr>
</table>
