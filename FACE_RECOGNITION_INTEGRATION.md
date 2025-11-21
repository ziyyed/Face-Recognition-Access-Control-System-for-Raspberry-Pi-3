# Face Recognition System Integration with Flask Dashboard

## Overview

The face recognition system (`recognize_and_control_proteus.py`) now automatically logs all access attempts to the Flask Admin Dashboard.

## How It Works

1. **Face Recognition**: When a face is detected and recognized, the system gets a `label` (which is the `employee.id`)
2. **API Call**: The system calls `POST http://localhost:5000/api/check-access` with the face_id
3. **Logging**: The Flask API logs the attempt to the database and returns the access decision
4. **Dashboard**: All logs appear in the dashboard's "Logs" page

## Setup

### 1. Install Dependencies

Make sure `requests` is installed:
```bash
pip install requests
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### 2. Start Flask Dashboard

In one terminal:
```bash
python app.py
```

The Flask app will run on `http://localhost:5000`

### 3. Start Face Recognition System

In another terminal:
```bash
python recognize_and_control_proteus.py --proteus-port COM2
```

## What Gets Logged

- **Recognized Faces**: When a face is recognized (label != -1), the system logs:
  - Employee ID (face_id)
  - Access decision (Granted/Denied based on schedule)
  - Timestamp

- **Unknown Faces**: When a face is not recognized (label == -1), the system logs:
  - Status: Denied
  - Reason: "Unknown face - not recognized"
  - Timestamp

## Viewing Logs

1. Open the Flask dashboard: `http://localhost:5000`
2. Click on **"Logs"** in the navigation
3. You'll see all access attempts with:
   - Timestamp
   - Employee name
   - Status (Granted/Denied)
   - Position

## Important Notes

1. **Employee ID Mapping**: The `label` from face recognition must match the `employee.id` in the database. When training, the system uses `employee.id` as the label.

2. **API URL**: The default API URL is `http://localhost:5000/api/check-access`. If your Flask app runs on a different host/port, update `FLASK_API_URL` in `recognize_and_control_proteus.py`.

3. **Error Handling**: If the Flask API is not available, the face recognition system will continue to work but won't log to the dashboard. You'll see a warning message.

4. **Duplicate Prevention**: The system only logs once per face recognition to avoid spam. It tracks the last logged face_id.

## Troubleshooting

### Logs Not Appearing

1. **Check Flask is Running**: Make sure `python app.py` is running
2. **Check API URL**: Verify `FLASK_API_URL` in `recognize_and_control_proteus.py` matches your Flask server
3. **Check Network**: Ensure both processes can communicate (localhost should work)
4. **Check Console**: Look for warning messages in the face recognition console

### API Connection Errors

If you see `[WARN] Could not connect to Flask API`:
- Flask app might not be running
- Wrong URL/port in `FLASK_API_URL`
- Firewall blocking the connection

## Configuration

You can change the Flask API URL by modifying this line in `recognize_and_control_proteus.py`:

```python
FLASK_API_URL = "http://localhost:5000/api/check-access"
```

For remote Flask server:
```python
FLASK_API_URL = "http://192.168.1.100:5000/api/check-access"
```

## API Response Format

The Flask API returns:

**For Granted Access:**
```json
{
    "status": "Granted",
    "employee_name": "Alice"
}
```

**For Denied Access:**
```json
{
    "status": "Denied",
    "employee_name": "Bob",
    "reason": "Outside scheduled access hours"
}
```

**For Unknown Face:**
```json
{
    "status": "Denied",
    "employee_name": null,
    "reason": "Unknown face - not recognized"
}
```

