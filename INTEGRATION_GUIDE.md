# Flask Admin Dashboard - Integration Guide

## Overview

This Flask Admin Dashboard provides a complete web interface for managing the Face Recognition Access Control System. It integrates directly with the Raspberry Pi hardware through a service layer architecture.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Flask Web Application (app.py)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Dashboard  │  │  Employees  │  │ Access Rules │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Service Layer (services.py)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │FaceCapture   │  │ModelTrainer  │  │AccessControl │  │
│  │  Service     │  │  Service     │  │  Service     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
   Camera/OpenCV      Dataset Files        Database Models
```

## Key Features

### 1. **Service Layer Architecture**
- **FaceCaptureService**: Handles camera operations with thread safety
- **ModelTrainerService**: Trains LBPH face recognizer on dataset
- **AccessControlService**: Verifies access based on time/day rules

### 2. **Database Models**
- **Employee**: Stores employee information (id, name, position)
- **AccessRule**: Defines time-based access schedules (day, start_time, end_time)
- **AccessLog**: Records all access attempts (timestamp, status, employee)

### 3. **Web Interface**
- **Dashboard**: System status, statistics, latest logs
- **Employee Management**: Add/delete employees with automatic face capture
- **Access Rules**: Define time-based access schedules per employee
- **Logs**: View all access attempts with pagination

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Access at: `http://localhost:5000`

## Workflow

### Adding an Employee

1. Go to **Employees** page
2. Click **Add Employee**
3. Enter name and position
4. Submit form
5. System automatically:
   - Saves employee to database
   - Opens camera and captures 50 face images
   - Saves images to `dataset/User.{id}/User.{id}.{count}.jpg`
   - Trains the recognition model
   - Saves `trainer.yml` and `labels.json`

### Setting Access Rules

1. Go to **Employees** page
2. Click **Access** button for an employee
3. Click **Add Rule**
4. Select day of week, start time, end time
5. Submit

### Retraining an Employee

1. Go to **Employees** page
2. Click **Retrain** button
3. System captures new face images
4. Model is retrained automatically

### Deleting an Employee

1. Go to **Employees** page
2. Click **Delete** button
3. System:
   - Deletes employee from database
   - Deletes `dataset/User.{id}/` directory
   - Retrains model to remove employee

## API Integration

### POST /api/check-access

The face recognition system should call this endpoint after detecting a face.

**Request:**
```json
{
    "face_id": 123
}
```

**Response (Granted):**
```json
{
    "status": "Granted",
    "employee_name": "Alice"
}
```

**Response (Denied):**
```json
{
    "status": "Denied",
    "employee_name": "Bob",
    "reason": "Outside scheduled access hours"
}
```

### Integration with recognize_and_control_proteus.py

Modify the face recognition script to call the Flask API:

```python
import requests

# After face recognition
face_id = prediction.label  # From LBPH recognizer

try:
    response = requests.post(
        'http://localhost:5000/api/check-access',
        json={'face_id': face_id},
        timeout=2
    )
    result = response.json()
    
    if result['status'] == 'Granted':
        show_message(lcd, "Bienvenue", result['employee_name'])
        door.open_door(DOOR_OPEN_SECONDS)
    else:
        show_message(lcd, "Acces refuse", result.get('reason', ''))
        door.close_door()
except Exception as e:
    show_message(lcd, "Erreur systeme")
    door.close_door()
```

## File Structure

```
.
├── app.py                 # Main Flask application
├── models.py              # Database models (Employee, AccessRule, AccessLog)
├── services.py            # Service layer (FaceCapture, ModelTrainer, AccessControl)
├── requirements.txt       # Python dependencies
├── templates/
│   ├── base.html         # Base template with navigation
│   ├── dashboard.html    # Dashboard page
│   ├── employees.html    # Employee management
│   ├── access_rules.html # Access rules management
│   └── logs.html         # Attendance logs
└── dataset/              # Face images (created automatically)
    └── User.{id}/
        └── User.{id}.{count}.jpg
```

## Database Schema

### Employee
- `id` (Primary Key)
- `name` (String, required)
- `position` (String, optional)
- `created_at` (DateTime)

### AccessRule
- `id` (Primary Key)
- `employee_id` (Foreign Key → Employee)
- `day_of_week` (Integer, 0-6)
- `start_time` (Time)
- `end_time` (Time)

### AccessLog
- `id` (Primary Key)
- `employee_id` (Foreign Key → Employee, nullable)
- `timestamp` (DateTime)
- `status` (String: 'Granted' or 'Denied')
- `snapshot_path` (String, optional)

## Thread Safety

The `FaceCaptureService` uses a thread lock (`_camera_lock`) to ensure only one camera operation happens at a time. This prevents conflicts when multiple requests try to access the camera simultaneously.

## Important Notes

1. **Face ID Mapping**: The system uses `employee.id` as the face_id. When training, images are labeled with the employee ID, so the recognition system must return employee IDs.

2. **Camera Access**: The camera is opened only during face capture operations and is properly released afterward.

3. **Model Training**: The model is automatically retrained after:
   - Adding a new employee
   - Deleting an employee
   - Retraining an employee

4. **Access Control**: Access is granted only if:
   - Employee exists
   - Current day has an active rule
   - Current time is within rule's time window

## Troubleshooting

### Camera Not Opening
- Check camera permissions
- Ensure no other application is using the camera
- Try different camera index (0, 1, 2, etc.)

### Model Training Fails
- Ensure dataset directory exists
- Check that images are in correct format (User.{id}/User.{id}.{count}.jpg)
- Verify opencv-contrib-python is installed

### Access Always Denied
- Check that access rules are defined for the current day
- Verify current time is within rule's time window
- Check employee exists in database

## Production Deployment

For production use:

1. Set `SECRET_KEY` environment variable
2. Use a production WSGI server (gunicorn, uWSGI)
3. Configure proper database (PostgreSQL recommended)
4. Add authentication/authorization
5. Enable HTTPS
6. Set up proper logging
7. Configure reverse proxy (nginx)

