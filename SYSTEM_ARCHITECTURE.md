# System Architecture & How Everything Works

## Overview

The Flask Admin Dashboard is a web-based management system for the Face Recognition Access Control System. It manages employees, their access schedules, and logs all access attempts.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Flask Web Application                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Dashboard  │  │  Employees   │  │     Logs     │     │
│  │   (View)     │  │  (CRUD)      │  │   (View)     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────────────────────────────────────────┐     │
│  │         REST API: /api/check-access               │     │
│  │  (Used by Face Recognition System)                │     │
│  └──────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              SQLite Database (access_control.db)            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Employees   │  │   Schedules │  │     Logs     │     │
│  │   Table      │  │    Table     │  │    Table     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                          ▲
                          │
┌─────────────────────────────────────────────────────────────┐
│         Face Recognition System (Raspberry Pi)               │
│  - Detects face → Gets face_id                              │
│  - Calls POST /api/check-access with {face_id: 123}          │
│  - Receives authorization decision                           │
│  - Opens/closes door based on response                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Database Schema & Relationships

### 1. **Employee Table**
Stores registered employees in the system.

```python
Employee:
  - id (Primary Key)
  - name (e.g., "John Doe")
  - face_id (Unique, matches face recognition system)
  - department (Optional)
  - photo_path (Optional)
  - created_at (Timestamp)
```

**Relationships:**
- One Employee → Many AccessSchedules (one-to-many)
- One Employee → Many AttendanceLogs (one-to-many)

### 2. **AccessSchedule Table**
Defines when each employee can access the system.

```python
AccessSchedule:
  - id (Primary Key)
  - employee_id (Foreign Key → Employee)
  - day_of_week (0=Monday, 1=Tuesday, ..., 6=Sunday)
  - start_time (e.g., "09:00")
  - end_time (e.g., "17:00")
  - is_active (Boolean - can disable without deleting)
```

**Example:**
- Employee "Alice" can access:
  - Monday: 9:00 AM - 5:00 PM
  - Tuesday: 9:00 AM - 5:00 PM
  - Wednesday: 10:00 AM - 2:00 PM

### 3. **AttendanceLog Table**
Records every access attempt (granted or denied).

```python
AttendanceLog:
  - id (Primary Key)
  - employee_id (Foreign Key → Employee, nullable)
  - timestamp (When access was attempted)
  - access_granted (Boolean)
  - rejection_reason (Text, if denied)
```

**Why nullable employee_id?**
- If face_id is not found in database, employee_id is NULL
- Still logs the attempt for security/audit purposes

---

## 🔄 Data Flow: How Access Control Works

### Step-by-Step Process

#### **1. Employee Registration (Admin Dashboard)**
```
Admin → Employees Page → Add Employee
  ├─ Enter: Name, Face ID, Department
  ├─ Face ID must match face recognition system
  └─ Employee saved to database
```

#### **2. Schedule Setup (Admin Dashboard)**
```
Admin → Edit Employee → Add Schedule
  ├─ Select: Day of Week (Monday-Sunday)
  ├─ Set: Start Time, End Time
  ├─ Toggle: Active/Inactive
  └─ Multiple schedules per employee allowed
```

#### **3. Face Recognition Attempt (Raspberry Pi)**
```
Camera detects face
  ↓
Face recognition system identifies face_id (e.g., 123)
  ↓
Raspberry Pi makes HTTP POST request:
  POST http://flask-server:5000/api/check-access
  Body: {"face_id": 123}
  ↓
Flask API processes request...
```

#### **4. Access Check Logic (Flask API)**

```python
# Pseudo-code of what happens in /api/check-access

1. Receive face_id from request
2. Get current server time and day of week
   - current_time = datetime.now()
   - current_day = 0 (Monday) to 6 (Sunday)
   - current_time_only = "14:30"

3. Find Employee by face_id
   - If NOT FOUND → Log attempt, return DENIED

4. Find Active Schedules for this employee on current day
   - Query: AccessSchedule WHERE
     - employee_id = employee.id
     - day_of_week = current_day
     - is_active = True

5. Check if current time is within any schedule
   - For each schedule:
     - If start_time <= current_time <= end_time:
       → ACCESS GRANTED ✓
   - If no matching schedule:
     → ACCESS DENIED ✗

6. Log the attempt to AttendanceLog
   - Always log, whether granted or denied
   - Include rejection_reason if denied

7. Return JSON response
   - {"status": "authorized", "name": "Alice"}
   - OR {"status": "denied", "reason": "Outside scheduled hours"}
```

#### **5. Response Handling (Raspberry Pi)**
```
Raspberry Pi receives JSON response
  ├─ If status == "authorized"
  │   ├─ Display: "Welcome [Name]"
  │   ├─ Open door motor
  │   └─ Log success
  │
  └─ If status == "denied"
      ├─ Display: "Access Denied: [Reason]"
      ├─ Keep door closed
      └─ Log failure
```

---

## 🎯 Key Features Explained

### **1. Dashboard (`/`)**
- **Purpose**: Overview of system activity
- **Data Retrieved**:
  - Latest 10 attendance logs (most recent first)
  - Total employee count
  - Total access attempts today
- **How it works**: Simple database queries, no complex logic

### **2. Employee Management (`/employees`)**
- **CRUD Operations**:
  - **Create**: Add new employee with face_id
  - **Read**: View all employees in table
  - **Update**: Edit employee details (name, department, etc.)
  - **Delete**: Remove employee (cascades to schedules)
- **Schedule Management**:
  - Each employee can have multiple schedules
  - Schedules are day-specific (one per day)
  - Can be activated/deactivated without deletion

### **3. Attendance Logs (`/logs`)**
- **Purpose**: Audit trail of all access attempts
- **Features**:
  - Pagination (50 entries per page)
  - Shows: timestamp, employee, status, reason
  - Filters by date (can be extended)
- **Use Cases**:
  - Security audit
  - Attendance tracking
  - Troubleshooting access issues

### **4. API Endpoint (`/api/check-access`)**
- **Method**: POST
- **Input**: JSON with `face_id`
- **Output**: JSON with authorization status
- **Critical Logic**:
  1. Validates face_id exists
  2. Checks current day of week
  3. Validates current time against schedules
  4. Logs every attempt (for audit)
  5. Returns decision

---

## 🔐 Security & Validation

### **Input Validation**
- Face ID must be unique (enforced at database level)
- Face ID must be numeric
- Schedule times must be valid (start < end)
- All required fields validated before saving

### **Error Handling**
- Database transactions with rollback on errors
- User-friendly error messages via Flask flash
- API returns appropriate HTTP status codes

### **Data Integrity**
- Foreign key constraints ensure data consistency
- Cascade deletes: Deleting employee removes schedules
- Soft deletes: Schedules can be deactivated without deletion

---

## 🔌 Integration with Face Recognition System

### **Current System (recognize_and_control_proteus.py)**
The existing face recognition system needs to be modified to call the Flask API:

```python
# In recognize_and_control_proteus.py, after face recognition:

import requests

# When face is recognized and face_id is obtained
face_id = prediction.label  # From LBPH recognizer

# Call Flask API
try:
    response = requests.post(
        'http://localhost:5000/api/check-access',
        json={'face_id': face_id},
        timeout=2
    )
    result = response.json()
    
    if result['status'] == 'authorized':
        # Grant access
        show_message(lcd, "Bienvenue", result['name'])
        door.open_door(DOOR_OPEN_SECONDS)
    else:
        # Deny access
        show_message(lcd, "Acces refuse", result.get('reason', ''))
        door.close_door()
except Exception as e:
    # Fallback: deny on API error
    show_message(lcd, "Erreur systeme")
    door.close_door()
```

---

## 📈 Example Scenarios

### **Scenario 1: Employee Access During Work Hours**
```
Time: Monday, 10:30 AM
Employee: Alice (face_id: 123)
Schedule: Monday 9:00 AM - 5:00 PM

Flow:
1. Face detected → face_id = 123
2. API called with face_id = 123
3. System finds Alice
4. Finds schedule: Monday 9:00-17:00
5. Current time (10:30) is within schedule
6. Log: access_granted = True
7. Response: {"status": "authorized", "name": "Alice"}
8. Door opens ✓
```

### **Scenario 2: Employee Access Outside Hours**
```
Time: Monday, 7:00 AM
Employee: Alice (face_id: 123)
Schedule: Monday 9:00 AM - 5:00 PM

Flow:
1. Face detected → face_id = 123
2. API called with face_id = 123
3. System finds Alice
4. Finds schedule: Monday 9:00-17:00
5. Current time (7:00) is BEFORE start_time
6. Log: access_granted = False, reason = "Outside scheduled hours"
7. Response: {"status": "denied", "reason": "Outside scheduled hours"}
8. Door stays closed ✗
```

### **Scenario 3: Unknown Face**
```
Time: Monday, 2:00 PM
Face detected but not recognized (face_id: 999)
No employee with face_id = 999 in database

Flow:
1. Face detected → face_id = 999
2. API called with face_id = 999
3. System searches for employee → NOT FOUND
4. Log: access_granted = False, employee_id = NULL, reason = "Employee not found"
5. Response: {"status": "denied", "reason": "Employee not found"}
6. Door stays closed ✗
```

### **Scenario 4: No Schedule Defined**
```
Time: Saturday, 10:00 AM
Employee: Bob (face_id: 456)
No schedule defined for Saturday

Flow:
1. Face detected → face_id = 456
2. API called with face_id = 456
3. System finds Bob
4. Searches for Saturday schedule → NOT FOUND
5. Log: access_granted = False, reason = "No schedule defined for this day"
6. Response: {"status": "denied", "reason": "No schedule defined for this day"}
7. Door stays closed ✗
```

---

## 🛠️ Technical Details

### **Database Initialization**
- On first run, `app.py` checks if `access_control.db` exists
- If not, calls `init_db()` which creates all tables
- Uses SQLAlchemy ORM for database operations

### **Template Rendering**
- Jinja2 templates for HTML generation
- Bootstrap 5 for responsive UI
- HTMX for dynamic updates (optional, can be extended)

### **Session Management**
- Flask sessions for flash messages
- No authentication (can be added for production)

### **API Response Format**
```json
// Success
{
  "status": "authorized",
  "name": "Alice"
}

// Denied
{
  "status": "denied",
  "name": "Bob",
  "reason": "Outside scheduled hours"
}

// Error
{
  "status": "denied",
  "reason": "Invalid request: face_id required"
}
```

---

## 🚀 Future Enhancements

1. **Authentication**: Add login system for admin dashboard
2. **Real-time Updates**: WebSocket for live log updates
3. **Reports**: Generate attendance reports (daily, weekly, monthly)
4. **Notifications**: Email/SMS alerts for denied access
5. **Multi-location**: Support multiple access points
6. **Biometric Integration**: Direct integration with face recognition system

---

## 📝 Summary

The system works as a **centralized access control manager**:

1. **Admin** manages employees and schedules via web dashboard
2. **Face Recognition System** detects faces and queries Flask API
3. **Flask API** validates access based on schedules and logs everything
4. **Database** stores all data with proper relationships
5. **Logs** provide complete audit trail

The key innovation is **time-based access control** - employees can only access during their defined schedules, providing both security and attendance tracking.

