"""
Flask Admin Dashboard for Face Recognition Access Control System.

This application provides a web interface to manage employees, capture faces,
train the recognition model, and view access logs. It integrates directly with
the Raspberry Pi hardware through service classes.
"""

import os
import shutil
import csv
import io
from datetime import datetime, time as dt_time, timedelta
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file, make_response, send_from_directory
from sqlalchemy import func
from models import db, Employee, AccessRule, AccessLog
from services import FaceCaptureService, ModelTrainerService, AccessControlService

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///access_control.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Day names for display
DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# Initialize services
face_capture_service = FaceCaptureService()
model_trainer_service = ModelTrainerService()
dataset_dir = Path("dataset")


def init_db():
    """Initialize database tables."""
    with app.app_context():
        db.create_all()
        print("Database initialized successfully.")


def migrate_db():
    """Migrate existing database to new schema."""
    import sqlite3
    from pathlib import Path
    
    # Get database path from config
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if db_uri.startswith('sqlite:///'):
        # sqlite:/// means relative path (current directory)
        db_path_str = db_uri.replace('sqlite:///', '')
        db_path = Path(db_path_str) if db_path_str else Path("access_control.db")
    else:
        db_path = Path("access_control.db")
    
    if not db_path.exists():
        print(f"Database not found at {db_path}. Will be created with correct schema.")
        return  # No migration needed, database will be created fresh
    
    print(f"Checking database schema at: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if employees table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employees'")
        if not cursor.fetchone():
            print("Employees table doesn't exist. Will be created.")
            conn.close()
            return
        
        # Check if position column exists in employees table
        cursor.execute("PRAGMA table_info(employees)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Current columns in employees table: {columns}")
        
        if 'position' not in columns:
            print("Migrating database: Adding 'position' column to employees table...")
            cursor.execute("ALTER TABLE employees ADD COLUMN position VARCHAR(100)")
            conn.commit()
            print("✓ Migration complete: Added 'position' column")
        else:
            print("✓ Database schema is up to date")
        
        conn.close()
        
    except Exception as e:
        print(f"Migration error: {str(e)}")
        import traceback
        traceback.print_exc()


@app.route('/')
def dashboard():
    """Main dashboard showing statistics and system status."""
    # Get latest 5 access logs
    latest_logs = AccessLog.query.order_by(AccessLog.timestamp.desc()).limit(5).all()
    
    # Get total employees
    try:
        total_employees = Employee.query.count()
    except Exception:
        total_employees = 0
    
    # Check if model exists
    model_exists = model_trainer_service.model_exists()
    
    # Get total entries today
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    total_today = AccessLog.query.filter(AccessLog.timestamp >= today_start).count()
    
    # Chart Data: Access attempts for last 7 days
    dates = []
    counts = []
    for i in range(6, -1, -1):
        date = datetime.now().date() - timedelta(days=i)
        start = datetime.combine(date, dt_time.min)
        end = datetime.combine(date, dt_time.max)
        count = AccessLog.query.filter(AccessLog.timestamp >= start, AccessLog.timestamp <= end).count()
        dates.append(date.strftime('%Y-%m-%d'))
        counts.append(count)
    
    return render_template('dashboard.html',
                         latest_logs=latest_logs,
                         total_employees=total_employees,
                         total_today=total_today,
                         model_exists=model_exists,
                         day_names=DAY_NAMES,
                         chart_dates=dates,
                         chart_counts=counts)


@app.route('/logs/export')
def export_logs():
    """Export logs to CSV."""
    # Get filters from query params
    date_str = request.args.get('date')
    employee_id = request.args.get('employee_id', type=int)
    
    query = AccessLog.query
    
    if date_str:
        try:
            filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_of_day = datetime.combine(filter_date, dt_time.min)
            end_of_day = datetime.combine(filter_date, dt_time.max)
            query = query.filter(AccessLog.timestamp >= start_of_day, AccessLog.timestamp <= end_of_day)
        except ValueError:
            pass
            
    if employee_id:
        query = query.filter(AccessLog.employee_id == employee_id)
        
    logs = query.order_by(AccessLog.timestamp.desc()).all()
    
    # Create CSV
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Timestamp', 'Employee ID', 'Employee Name', 'Position', 'Status'])
    
    for log in logs:
        emp_name = log.employee.name if log.employee else 'Unknown'
        emp_pos = log.employee.position if log.employee and log.employee.position else '-'
        cw.writerow([
            log.id,
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.employee_id or '-',
            emp_name,
            emp_pos,
            log.status
        ])
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=access_logs.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@app.route('/employee/<int:employee_id>/photo')
def employee_photo(employee_id):
    """Serve the first available photo for an employee."""
    user_dir = dataset_dir / f"User.{employee_id}"
    if user_dir.exists():
        # Find first jpg
        photos = list(user_dir.glob("*.jpg"))
        if photos:
            return send_from_directory(user_dir, photos[0].name)
    
    # Return a placeholder or 404
    # For now, let's return a simple 404 if no photo, 
    # the frontend can handle the broken image or we can serve a static placeholder
    return "No photo", 404


@app.route('/employees')
def employees():
    """Employee management page."""
    try:
        employees_list = Employee.query.order_by(Employee.name).all()
    except Exception as e:
        if 'no such column: employees.position' in str(e) or 'position' in str(e):
            # Auto-fix: add missing column
            print("Auto-fixing database: Adding missing 'position' column...")
            from sqlalchemy import text
            try:
                db.session.execute(text("ALTER TABLE employees ADD COLUMN position VARCHAR(100)"))
                db.session.commit()
                print("✓ Added 'position' column")
            except Exception as sql_err:
                if 'duplicate column' not in str(sql_err).lower():
                    print(f"Migration note: {sql_err}")
                db.session.rollback()
            employees_list = Employee.query.order_by(Employee.name).all()
        else:
            raise
    
    return render_template('employees.html', employees=employees_list, day_names=DAY_NAMES)


@app.route('/employees/add', methods=['POST'])
def add_employee():
    """Add a new employee and capture their face."""
    try:
        name = request.form.get('name', '').strip()
        position = request.form.get('position', '').strip()
        
        if not name:
            flash('Name is required.', 'error')
            return redirect(url_for('employees'))
        
        # Create employee in database
        employee = Employee(
            name=name,
            position=position if position else None
        )
        
        db.session.add(employee)
        try:
            db.session.commit()
        except Exception as db_error:
            # Check if it's the face_id constraint error
            if 'face_id' in str(db_error) and 'NOT NULL' in str(db_error):
                flash('Database schema error detected. Fixing automatically...', 'warning')
                # Auto-fix: recreate table without face_id
                from sqlalchemy import text
                try:
                    # Get existing data
                    result = db.session.execute(text("SELECT id, name, created_at FROM employees"))
                    employees_data = result.fetchall()
                    
                    # Recreate table
                    db.session.execute(text("DROP TABLE IF EXISTS employees_old"))
                    db.session.execute(text("ALTER TABLE employees RENAME TO employees_old"))
                    
                    db.session.execute(text("""
                        CREATE TABLE employees (
                            id INTEGER NOT NULL PRIMARY KEY,
                            name VARCHAR(100) NOT NULL,
                            position VARCHAR(100),
                            created_at DATETIME
                        )
                    """))
                    
                    # Restore data
                    for emp in employees_data:
                        db.session.execute(text("""
                            INSERT INTO employees (id, name, created_at)
                            VALUES (:id, :name, :created_at)
                        """), {'id': emp[0], 'name': emp[1], 'created_at': emp[2]})
                    
                    db.session.execute(text("DROP TABLE employees_old"))
                    db.session.commit()
                    
                    # Retry adding employee
                    db.session.add(employee)
                    db.session.commit()
                    flash('Database schema fixed. Employee added.', 'success')
                except Exception as fix_error:
                    db.session.rollback()
                    flash(f'Error fixing database: {str(fix_error)}. Please run fix_face_id_column.py', 'error')
                    return redirect(url_for('employees'))
            else:
                raise
        
        # Get the employee ID after commit
        user_id = employee.id
        
        # IMMEDIATELY capture faces
        flash(f'Employee {name} added. Starting face capture...', 'info')
        capture_result = face_capture_service.capture_faces(user_id)
        
        if not capture_result['success']:
            flash(f'Face capture failed: {capture_result["message"]}', 'error')
            return redirect(url_for('employees'))
        
        # THEN train the model
        flash(f'Face capture completed ({capture_result["captured"]} images). Training model...', 'info')
        train_result = model_trainer_service.train_recognizer()
        
        if train_result['success']:
            flash(f'Employee {name} added successfully! Model retrained with {train_result["images_trained"]} images.', 'success')
        else:
            flash(f'Employee added but model training failed: {train_result["message"]}', 'warning')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding employee: {str(e)}', 'error')
    
    return redirect(url_for('employees'))


@app.route('/employees/<int:employee_id>/delete', methods=['POST'])
def delete_employee(employee_id):
    """Delete an employee and their dataset."""
    try:
        employee = Employee.query.get_or_404(employee_id)
        name = employee.name
        
        # Delete dataset directory
        user_dir = dataset_dir / f"User.{employee_id}"
        if user_dir.exists():
            shutil.rmtree(user_dir)
            app.logger.info(f"Deleted dataset directory: {user_dir}")
        
        # Delete from database
        db.session.delete(employee)
        db.session.commit()
        
        # Retrain model to remove this user
        train_result = model_trainer_service.train_recognizer()
        
        if train_result['success']:
            flash(f'Employee {name} deleted. Model retrained.', 'success')
        else:
            flash(f'Employee {name} deleted but model retraining failed.', 'warning')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting employee: {str(e)}', 'error')
    
    return redirect(url_for('employees'))


@app.route('/employees/<int:employee_id>/retrain', methods=['POST'])
def retrain_employee(employee_id):
    """Retrain the model for a specific employee."""
    try:
        employee = Employee.query.get_or_404(employee_id)
        
        # Capture new faces
        capture_result = face_capture_service.capture_faces(employee_id)
        
        if not capture_result['success']:
            flash(f'Face capture failed: {capture_result["message"]}', 'error')
            return redirect(url_for('employees'))
        
        # Train model
        train_result = model_trainer_service.train_recognizer()
        
        if train_result['success']:
            flash(f'Employee {employee.name} retrained successfully!', 'success')
        else:
            flash(f'Retraining failed: {train_result["message"]}', 'error')
            
    except Exception as e:
        flash(f'Error retraining employee: {str(e)}', 'error')
    
    return redirect(url_for('employees'))


@app.route('/employee/<int:employee_id>/access')
def employee_access_rules(employee_id):
    """View and manage access rules for an employee."""
    employee = Employee.query.get_or_404(employee_id)
    rules = AccessRule.query.filter_by(employee_id=employee_id).order_by(
        AccessRule.day_of_week, AccessRule.start_time
    ).all()
    
    return render_template('access_rules.html',
                         employee=employee,
                         rules=rules,
                         day_names=DAY_NAMES)


@app.route('/employee/<int:employee_id>/access/add', methods=['POST'])
def add_access_rule(employee_id):
    """Add an access rule for an employee."""
    try:
        employee = Employee.query.get_or_404(employee_id)
        
        day_of_week = int(request.form.get('day_of_week'))
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
        
        if start_time >= end_time:
            flash('Start time must be before end time.', 'error')
            return redirect(url_for('employee_access_rules', employee_id=employee_id))
        
        # Check for overlapping rules
        existing = AccessRule.query.filter_by(
            employee_id=employee_id,
            day_of_week=day_of_week
        ).all()
        
        for rule in existing:
            if (start_time < rule.end_time and end_time > rule.start_time):
                flash(f'Overlapping schedule exists for {DAY_NAMES[day_of_week]}.', 'error')
                return redirect(url_for('employee_access_rules', employee_id=employee_id))
        
        rule = AccessRule(
            employee_id=employee_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time
        )
        
        db.session.add(rule)
        db.session.commit()
        
        flash(f'Access rule added for {DAY_NAMES[day_of_week]}.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding access rule: {str(e)}', 'error')
    
    return redirect(url_for('employee_access_rules', employee_id=employee_id))


@app.route('/access-rules/<int:rule_id>/delete', methods=['POST'])
def delete_access_rule(rule_id):
    """Delete an access rule."""
    try:
        rule = AccessRule.query.get_or_404(rule_id)
        employee_id = rule.employee_id
        db.session.delete(rule)
        db.session.commit()
        flash('Access rule deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting access rule: {str(e)}', 'error')
    
    return redirect(url_for('employee_access_rules', employee_id=employee_id))


@app.route('/employees/<int:employee_id>/edit', methods=['POST'])
def edit_employee(employee_id):
    """Edit an employee's details."""
    try:
        employee = Employee.query.get_or_404(employee_id)
        name = request.form.get('name', '').strip()
        position = request.form.get('position', '').strip()
        
        if not name:
            flash('Name is required.', 'error')
            return redirect(url_for('employees'))
            
        employee.name = name
        employee.position = position if position else None
        
        db.session.commit()
        flash(f'Employee details updated successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating employee: {str(e)}', 'error')
    
    return redirect(url_for('employees'))


@app.route('/logs')
def logs():
    """View all attendance logs with filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Filters
    date_str = request.args.get('date')
    employee_id = request.args.get('employee_id', type=int)
    
    query = AccessLog.query
    
    if date_str:
        try:
            filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            # Filter by day (start of day to end of day)
            start_of_day = datetime.combine(filter_date, dt_time.min)
            end_of_day = datetime.combine(filter_date, dt_time.max)
            query = query.filter(AccessLog.timestamp >= start_of_day, AccessLog.timestamp <= end_of_day)
        except ValueError:
            pass
            
    if employee_id:
        query = query.filter(AccessLog.employee_id == employee_id)
    
    logs = query.order_by(AccessLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get all employees for the filter dropdown
    employees = Employee.query.order_by(Employee.name).all()
    
    return render_template('logs.html', 
                         logs=logs, 
                         day_names=DAY_NAMES,
                         employees=employees,
                         current_date=date_str,
                         current_employee=employee_id)


@app.route('/api/check-access', methods=['POST'])
def check_access():
    """
    API endpoint to check if an employee has access based on face_id and schedule.
    
    Expected JSON input:
    {
        "face_id": 123
    }
    
    Returns JSON response:
    {
        "status": "Granted" | "Denied",
        "employee_name": "Employee Name",
        "reason": "Reason (if denied)"
    }
    """
    try:
        data = request.get_json()
        if not data or 'face_id' not in data:
            return jsonify({
                'status': 'Denied',
                'reason': 'Invalid request: face_id required'
            }), 400
        
        face_id = int(data['face_id'])
        
        # Handle unknown face (face_id = -1)
        if face_id == -1:
            # Log unknown face attempt
            log = AccessLog(
                employee_id=None,
                status='Denied',
                snapshot_path=None
            )
            db.session.add(log)
            db.session.commit()
            
            return jsonify({
                'status': 'Denied',
                'employee_name': None,
                'reason': 'Unknown face - not recognized'
            }), 200
        
        # Use AccessControlService to verify
        access_service = AccessControlService()
        result = access_service.verify_access(face_id)
        
        # Log the access attempt
        employee = Employee.query.filter_by(id=face_id).first() if result['employee_name'] else None
        
        log = AccessLog(
            employee_id=employee.id if employee else None,
            status='Granted' if result['granted'] else 'Denied',
            snapshot_path=None  # Can be added if snapshot is captured
        )
        db.session.add(log)
        db.session.commit()
        
        if result['granted']:
            return jsonify({
                'status': 'Granted',
                'employee_name': result['employee_name']
            }), 200
        else:
            return jsonify({
                'status': 'Denied',
                'employee_name': result.get('employee_name'),
                'reason': result.get('reason', 'Access denied')
            }), 200
            
    except ValueError:
        return jsonify({
            'status': 'Denied',
            'reason': 'Invalid face_id format'
        }), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in check_access: {str(e)}")
        return jsonify({
            'status': 'Denied',
            'reason': f'Server error: {str(e)}'
        }), 500


@app.route('/api/train-model', methods=['POST'])
def train_model():
    """API endpoint to manually trigger model training."""
    try:
        result = model_trainer_service.train_recognizer()
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'users_trained': result['users_trained'],
                'images_trained': result['images_trained']
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        app.logger.error(f"Error training model: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# Initialize database on app startup
def ensure_database_schema():
    """Ensure database has correct schema on startup."""
    with app.app_context():
        from sqlalchemy import text
        
        try:
            # Check if employees table exists and has old schema
            result = db.session.execute(text("PRAGMA table_info(employees)"))
            columns_info = result.fetchall()
            columns = {row[1]: row for row in columns_info}
            
            # Check for face_id column (old schema)
            if 'face_id' in columns:
                print("⚠ Detected old schema with face_id column. Migrating...")
                try:
                    # Get existing data
                    result = db.session.execute(text("SELECT id, name, created_at FROM employees"))
                    employees_data = result.fetchall()
                    
                    # Recreate table with correct schema
                    db.session.execute(text("DROP TABLE IF EXISTS employees_old"))
                    db.session.execute(text("ALTER TABLE employees RENAME TO employees_old"))
                    
                    db.session.execute(text("""
                        CREATE TABLE employees (
                            id INTEGER NOT NULL PRIMARY KEY,
                            name VARCHAR(100) NOT NULL,
                            position VARCHAR(100),
                            created_at DATETIME
                        )
                    """))
                    
                    # Migrate data
                    for emp in employees_data:
                        db.session.execute(text("""
                            INSERT INTO employees (id, name, created_at)
                            VALUES (:id, :name, :created_at)
                        """), {'id': emp[0], 'name': emp[1], 'created_at': emp[2]})
                    
                    db.session.execute(text("DROP TABLE employees_old"))
                    db.session.commit()
                    print("✓ Migrated employees table (removed face_id)")
                except Exception as e:
                    db.session.rollback()
                    print(f"Migration error: {e}")
            
            # Check for position column
            if 'position' not in columns:
                print("Adding 'position' column...")
                try:
                    db.session.execute(text("ALTER TABLE employees ADD COLUMN position VARCHAR(100)"))
                    db.session.commit()
                    print("✓ Added 'position' column")
                except Exception as sql_err:
                    if 'duplicate column' not in str(sql_err).lower():
                        print(f"Note: {sql_err}")
                    db.session.rollback()
                    
        except Exception as e:
            # Table doesn't exist yet, will be created by db.create_all()
            pass
        
        # Ensure all tables exist with correct schema
        db.create_all()

# Run on module import
ensure_database_schema()


if __name__ == '__main__':
    # Migrate existing database or create new one before starting server
    with app.app_context():
        migrate_db()  # Check and migrate if needed
        db.create_all()  # Ensure all tables exist
    
    app.run(debug=True, host='0.0.0.0', port=5000)
