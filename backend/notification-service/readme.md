# Notification Service

A microservice for managing in-app notifications and scheduling task deadline reminders.

## Features

- **Automated Task Deadline Reminders**: Background scheduler checks task deadlines every hour
- **User Preference Integration**: Respects user notification preferences (channel, reminder times)
- **In-App Notifications**: Creates and manages in-app notifications in Firebase
- **Smart Deduplication**: Prevents sending duplicate notifications within 24 hours
- **RESTful API**: Full CRUD operations for notifications

## Architecture

### Background Scheduler
- Runs every hour using APScheduler
- Checks all incomplete tasks against user notification preferences
- Creates notifications when:
  - Task deadline matches user's reminder times (e.g., 7, 3, 1 days before)
  - User has in-app notifications enabled
  - No duplicate notification sent in last 24 hours

### Database Schema

**Firebase Path**: `notifications/{userId}/{notificationId}`

```json
{
  "notificationId": "auto-generated-id",
  "userId": "user-id",
  "taskId": "task-id",
  "type": "task_deadline_reminder",
  "title": "Task Deadline Approaching",
  "message": "Task 'Build Feature X' is due in 3 days",
  "taskTitle": "Build Feature X",
  "taskDeadline": 1728000000,
  "daysUntilDeadline": 3,
  "read": false,
  "createdAt": 1727741000,
  "readAt": null
}
```

## API Endpoints

### Get All Notifications
```
GET /notifications/{userId}
```
Returns all notifications for a user, sorted by newest first.

**Response:**
```json
{
  "notifications": [...]
}
```

### Get Unread Notifications
```
GET /notifications/{userId}/unread
```
Returns only unread notifications for a user.

**Response:**
```json
{
  "notifications": [...],
  "count": 5
}
```

### Mark Notification as Read
```
PATCH /notifications/{userId}/{notificationId}/read
```
Marks a specific notification as read.

**Response:**
```json
{
  "message": "Notification marked as read",
  "notification": {...}
}
```

### Mark All Notifications as Read
```
PATCH /notifications/{userId}/mark-all-read
```
Marks all notifications as read for a user.

**Response:**
```json
{
  "message": "Marked 5 notifications as read",
  "count": 5
}
```

### Delete Notification
```
DELETE /notifications/{userId}/{notificationId}
```
Deletes a specific notification.

**Response:**
```json
{
  "message": "Notification deleted successfully"
}
```

### Trigger Scheduler Manually (Testing)
```
POST /scheduler/trigger
```
Manually triggers the deadline checker for testing purposes.

**Response:**
```json
{
  "message": "Scheduler triggered successfully"
}
```

### Health Check
```
GET /health
```
Returns service health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "notification-service"
}
```

## Dependencies

- **Flask**: Web framework
- **Flask-CORS**: Cross-origin resource sharing
- **Firebase Admin SDK**: Firebase Realtime Database integration
- **APScheduler**: Background task scheduling

## Configuration

### Environment Variables
- `JSON_PATH`: Path to Firebase service account credentials
- `DATABASE_URL`: Firebase Realtime Database URL

### Scheduler Settings
- **Interval**: 1 hour (configurable in `start_scheduler()`)
- **Tolerance**: ±0.5 days for matching reminder times

## Usage

### Running Locally
```bash
cd notification-service
pip install -r requirements.txt
export JSON_PATH="/path/to/firebase-cred.json"
export DATABASE_URL="https://your-firebase-url.firebasedatabase.app/"
python app.py
```

### Running with Docker
```bash
docker-compose up notification-service
```

## Integration with Frontend

The notification service works with the existing notification preferences saved by users:

1. User sets preferences in Settings page (frontend)
2. Preferences stored in Firebase: `notificationPreferences/{userId}`
3. Notification service reads preferences and creates notifications
4. Frontend can fetch notifications via API

## Testing

### Manual Trigger
```bash
curl -X POST http://localhost:6004/scheduler/trigger
```

### Get Notifications
```bash
curl http://localhost:6004/notifications/{userId}
```

### Get Unread Count
```bash
curl http://localhost:6004/notifications/{userId}/unread
```

## Future Enhancements

- Email notification support
- Push notifications
- Notification templates
- Configurable scheduler intervals
- Notification history and analytics
- Batch notification operations
