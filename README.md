# Face Recognition Access Control System

A comprehensive Raspberry Pi 3-based face recognition access control system with **Flask Admin Dashboard**, LCD display, and door motor control. The system uses OpenCV's LBPH face recognizer to identify authorized users, enforces time-based access schedules, and provides a complete web interface for management.

## 🎯 Features

### Core System
- **Face Recognition**: Uses LBPH (Local Binary Patterns Histograms) face recognizer
- **Time-Based Access Control**: Enforces access schedules based on day of week and time windows
- **Password Authentication**: Two-factor authentication (face + password)
- **LCD Display**: Shows welcome messages or access denied on 16x2 LCD
- **Motor Control**: Controls door motor for authorized users
- **Proteus Simulation**: Full hardware simulation support via Proteus VSM

### Flask Admin Dashboard
- **Web Interface**: Complete Bootstrap 5 admin dashboard
- **Employee Management**: Add, edit, delete employees with automatic face capture
- **Access Schedule Management**: Define time-based access rules per employee
- **Attendance Logs**: View all access attempts with pagination and filtering
- **Real-time Integration**: Face recognition system automatically logs to dashboard
- **Service Layer Architecture**: Clean separation of concerns with service classes

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│         Face Recognition System (Raspberry Pi)          │
│  - Detects faces → Gets face_id                         │
│  - Calls Flask API → Checks schedule                    │
│  - Controls door based on response                      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼ HTTP POST
┌─────────────────────────────────────────────────────────┐
│              Flask Admin Dashboard                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Dashboard  │  │  Employees  │  │ Access Rules│   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Service Layer (services.py)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │FaceCapture   │  │ModelTrainer  │  │AccessControl │   │
│  │  Service     │  │  Service     │  │  Service     │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              SQLite Database                             │
│  - Employees, AccessRules, AccessLogs                    │
└─────────────────────────────────────────────────────────┘
```

## 📋 Hardware Requirements

- Raspberry Pi 3
- USB Camera or Pi Camera
- 16x2 LCD (parallel interface)
- DC Motor with driver (L293D or transistor/relay)
- Motor driver circuit

## 💻 Software Requirements

- Python 3.9+
- OpenCV (opencv-contrib-python)
- Flask 3.0+
- SQLAlchemy
- RPi.GPIO (for real hardware)
- pyserial (for Proteus communication)
- requests (for API integration)

## 🚀 Installation

### 1. Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# For Raspberry Pi hardware (if not using Proteus)
pip install RPi.GPIO RPLCD
```

### 2. Start Flask Admin Dashboard

```bash
# Start the Flask web server
python app.py
```

Access the dashboard at: `http://localhost:5000`

### 3. Add Employees via Dashboard

1. Open `http://localhost:5000` in your browser
2. Go to **Employees** page
3. Click **Add Employee**
4. Enter name and position
5. System automatically:
   - Captures 50 face images from camera
   - Trains the recognition model
   - Saves `trainer.yml` and `labels.json`

### 4. Set Access Schedules

1. Click **Access** button for an employee
2. Add access rules (e.g., Monday 9:00 AM - 5:00 PM)
3. Define multiple schedules per employee

### 5. Run Face Recognition System

**For Proteus simulation:**
```bash
python recognize_and_control_proteus.py --proteus-port COM2
```

**For real hardware:**
```bash
python recognize_and_control.py
```

**For testing without hardware:**
```bash
python recognize_and_control.py --mock-hardware
```

## 📖 Usage

### Traditional Method (Command Line)

If you prefer using command line tools:

```bash
# 1. Capture face dataset
python capture_dataset.py --username alice --num-images 80

# 2. Train the model
python train_model.py

# 3. Run recognition system
python recognize_and_control_proteus.py --proteus-port COM2
```

### Web Dashboard Method (Recommended)

1. **Start Flask Dashboard**: `python app.py`
2. **Add Employees**: Use the web interface to add employees (automatic face capture)
3. **Set Schedules**: Define access rules via web interface
4. **Run Recognition**: Start the face recognition system
5. **View Logs**: Check dashboard for all access attempts

## 🔌 API Integration

The face recognition system automatically calls the Flask API:

**Endpoint**: `POST /api/check-access`

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

The system is already integrated - no additional configuration needed!

## 📁 Project Structure

```
Face-Recognition-Access-Control-System/
├── app.py                          # Flask admin dashboard
├── models.py                       # Database models
├── services.py                     # Service layer (FaceCapture, ModelTrainer, AccessControl)
├── requirements.txt                # Python dependencies
├── templates/                      # Flask templates
│   ├── base.html                  # Base template
│   ├── dashboard.html             # Dashboard page
│   ├── employees.html             # Employee management
│   ├── access_rules.html          # Access rules management
│   └── logs.html                  # Attendance logs
├── capture_dataset.py             # Legacy: Capture face images (CLI)
├── train_model.py                 # Legacy: Train model (CLI)
├── recognize_and_control.py       # Main recognition (real hardware)
├── recognize_and_control_proteus.py  # Recognition (Proteus) - Integrated with Flask
├── Proteus_program_face_recognition.py  # Proteus VSM program
├── lcd_display.py                 # LCD control module
├── door_control.py                # Motor/door control module
├── dataset/                       # Face image dataset
│   └── User.{id}/                 # Per-employee images
│       └── User.{id}.{count}.jpg
├── trainer.yml                    # Trained model (generated)
├── labels.json                    # Employee ID to name mapping (generated)
├── access_control.db              # SQLite database (generated)
└── README.md                      # This file
```

## 🔧 Configuration

### Pin Configuration (BOARD Mode)

- **LCD**: RS=7, E=11, D4=12, D5=13, D6=15, D7=16
- **Motor**: Motor_1=29, Motor_2=31

### Flask API URL

Default: `http://localhost:5000/api/check-access`

To change, edit `FLASK_API_URL` in `recognize_and_control_proteus.py`

### Database

- Default: SQLite (`access_control.db`)
- Change via `DATABASE_URL` environment variable
- Auto-migrates on startup

## 📊 Database Schema

### Employee
- `id`: Primary key (used as face_id)
- `name`: Employee name
- `position`: Job position (optional)
- `created_at`: Registration timestamp

### AccessRule
- `id`: Primary key
- `employee_id`: Foreign key to Employee
- `day_of_week`: 0-6 (0=Monday, 6=Sunday)
- `start_time`: Access start time
- `end_time`: Access end time

### AccessLog
- `id`: Primary key
- `employee_id`: Foreign key to Employee (nullable)
- `timestamp`: Access attempt timestamp
- `status`: 'Granted' or 'Denied'
- `snapshot_path`: Optional image path

## 🔐 Access Control Flow

1. **Face Detected** → Recognition system identifies face_id
2. **API Call** → System calls Flask API with face_id
3. **Schedule Check** → Flask checks if current time is within employee's schedule
4. **Decision**:
   - **Granted**: Request password, then open door
   - **Denied**: Show denial message, keep door closed
5. **Logging** → All attempts logged to database
6. **Dashboard** → View logs in real-time via web interface

## 📚 Documentation

- **FLASK_ADMIN_README.md**: Flask dashboard documentation
- **INTEGRATION_GUIDE.md**: Complete integration guide
- **SYSTEM_ARCHITECTURE.md**: Detailed system architecture
- **FACE_RECOGNITION_INTEGRATION.md**: Face recognition integration details
- **PROTEUS_SETUP_GUIDE.md**: Proteus VSM setup instructions

## 🐛 Troubleshooting

### Database Schema Issues

If you get "no such column" errors:
```bash
python fix_database_force.py
```

### Camera Not Opening

- Check camera permissions
- Ensure no other app is using the camera
- Try different camera index

### Flask API Not Responding

- Ensure Flask app is running: `python app.py`
- Check API URL in `recognize_and_control_proteus.py`
- Verify firewall settings

### Access Always Denied

- Check access rules are defined for current day
- Verify current time is within schedule window
- Check employee exists in database

## 🔄 Migration from Old System

If you have an existing system:

1. Run database migration: `python fix_database_force.py`
2. Update labels.json: Retrain model via dashboard
3. Start Flask dashboard: `python app.py`
4. Face recognition system will automatically integrate

## 🚀 Production Deployment

For production:

1. Set `SECRET_KEY` environment variable
2. Use production WSGI server (gunicorn, uWSGI)
3. Configure PostgreSQL (instead of SQLite)
4. Add authentication/authorization
5. Enable HTTPS
6. Set up proper logging
7. Configure reverse proxy (nginx)

## 📝 License

This project is for educational purposes.

## 👤 Author

Face Recognition Access Control System - Raspberry Pi 3 Project

## 🙏 Acknowledgments

- OpenCV for face recognition capabilities
- Flask for web framework
- Bootstrap for UI components
