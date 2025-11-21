# Flask Admin Dashboard - Face Recognition Access Control System

A complete Flask web application for managing employees, access schedules, and viewing attendance logs for the Face Recognition Access Control System.

## Features

- **Dashboard**: Overview with statistics and latest access logs
- **Employee Management**: Full CRUD operations for employees
- **Access Schedule Management**: Define time-based access schedules for each employee
- **Attendance Logs**: View all access attempts with pagination
- **REST API**: JSON endpoint for face recognition system to check access

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

The application will automatically create the SQLite database (`access_control.db`) on first run.

3. Access the dashboard at: `http://localhost:5000`

## API Endpoint

### POST /api/check-access

Check if an employee has access based on face_id and current schedule.

**Request:**
```json
{
    "face_id": 123
}
```

**Response (Authorized):**
```json
{
    "status": "authorized",
    "name": "Alice"
}
```

**Response (Denied):**
```json
{
    "status": "denied",
    "name": "Alice",
    "reason": "Outside scheduled hours"
}
```

The endpoint automatically logs all access attempts to the `AttendanceLog` table.

## Database Schema

### Employee
- `id`: Primary key
- `name`: Employee name
- `face_id`: Unique face recognition ID (must match face recognition system)
- `department`: Optional department name
- `photo_path`: Optional path to employee photo
- `created_at`: Timestamp

### AccessSchedule
- `id`: Primary key
- `employee_id`: Foreign key to Employee
- `day_of_week`: 0-6 (0=Monday, 6=Sunday)
- `start_time`: Access start time (HH:MM)
- `end_time`: Access end time (HH:MM)
- `is_active`: Boolean flag

### AttendanceLog
- `id`: Primary key
- `employee_id`: Foreign key to Employee (nullable)
- `timestamp`: Access attempt timestamp
- `access_granted`: Boolean
- `rejection_reason`: Text reason if denied

## Usage

1. **Add Employees**: Go to Employees page and click "Add Employee"
   - Enter name and face_id (must match the face recognition system)
   - Optionally add department and photo path

2. **Set Access Schedules**: Edit an employee and add access schedules
   - Select day of week
   - Set start and end times
   - Mark as active/inactive

3. **View Logs**: Check the Logs page to see all access attempts

4. **Integration**: The face recognition system should call `/api/check-access` with the detected face_id

## Configuration

- Database: SQLite (`access_control.db`) - can be changed via `DATABASE_URL` environment variable
- Secret Key: Set `SECRET_KEY` environment variable for production
- Port: Default 5000, can be changed in `app.py`

## File Structure

```
.
├── app.py                 # Main Flask application
├── models.py              # Database models
├── requirements.txt       # Python dependencies
├── templates/
│   ├── base.html         # Base template with navigation
│   ├── dashboard.html    # Dashboard page
│   ├── employees.html    # Employee management page
│   └── logs.html         # Attendance logs page
└── access_control.db     # SQLite database (created automatically)
```

## Notes

- The face_id must match the IDs used by your face recognition system
- Access is granted only if current time is within an active schedule for the current day
- All access attempts are logged regardless of outcome
- The system uses server time for schedule checking

