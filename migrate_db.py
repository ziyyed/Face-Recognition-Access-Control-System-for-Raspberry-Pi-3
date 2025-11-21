"""
Database migration script to update schema.

This script adds the 'position' column to the employees table
and ensures all new columns from the updated models are present.
"""

from app import app, db
from models import Employee, AccessRule, AccessLog
import sqlite3
from pathlib import Path

def migrate_database():
    """Migrate database to new schema."""
    db_path = Path("access_control.db")
    
    if not db_path.exists():
        print("Database doesn't exist. Creating new database...")
        with app.app_context():
            db.create_all()
        print("Database created successfully.")
        return
    
    print("Migrating database...")
    
    with app.app_context():
        # Connect directly to SQLite to check and modify schema
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        try:
            # Check if position column exists
            cursor.execute("PRAGMA table_info(employees)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'position' not in columns:
                print("Adding 'position' column to employees table...")
                cursor.execute("ALTER TABLE employees ADD COLUMN position VARCHAR(100)")
                conn.commit()
                print("✓ Added 'position' column")
            else:
                print("✓ 'position' column already exists")
            
            # Check if access_rules table exists (old schema might have access_schedules)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='access_schedules'")
            if cursor.fetchone():
                print("Renaming 'access_schedules' to 'access_rules'...")
                # SQLite doesn't support RENAME TABLE directly, so we need to recreate
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS access_rules_new (
                        id INTEGER NOT NULL PRIMARY KEY,
                        employee_id INTEGER NOT NULL,
                        day_of_week INTEGER NOT NULL,
                        start_time TIME NOT NULL,
                        end_time TIME NOT NULL,
                        FOREIGN KEY(employee_id) REFERENCES employees (id) ON DELETE CASCADE
                    )
                """)
                cursor.execute("INSERT INTO access_rules_new SELECT * FROM access_schedules")
                cursor.execute("DROP TABLE access_schedules")
                cursor.execute("ALTER TABLE access_rules_new RENAME TO access_rules")
                conn.commit()
                print("✓ Renamed table to 'access_rules'")
            
            # Check if access_logs table has correct columns
            cursor.execute("PRAGMA table_info(access_logs)")
            log_columns = [row[1] for row in cursor.fetchall()]
            
            # Check for old column names and update
            if 'access_granted' in log_columns:
                print("Updating access_logs table schema...")
                # Create new table with correct schema
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS access_logs_new (
                        id INTEGER NOT NULL PRIMARY KEY,
                        employee_id INTEGER,
                        timestamp DATETIME NOT NULL,
                        status VARCHAR(20) NOT NULL,
                        snapshot_path VARCHAR(255),
                        FOREIGN KEY(employee_id) REFERENCES employees (id) ON DELETE SET NULL
                    )
                """)
                # Migrate data: convert access_granted boolean to status string
                cursor.execute("""
                    INSERT INTO access_logs_new (id, employee_id, timestamp, status, snapshot_path)
                    SELECT 
                        id,
                        employee_id,
                        timestamp,
                        CASE WHEN access_granted = 1 THEN 'Granted' ELSE 'Denied' END,
                        NULL
                    FROM access_logs
                """)
                cursor.execute("DROP TABLE access_logs")
                cursor.execute("ALTER TABLE access_logs_new RENAME TO access_logs")
                cursor.execute("CREATE INDEX IF NOT EXISTS ix_access_logs_timestamp ON access_logs(timestamp)")
                conn.commit()
                print("✓ Updated access_logs table schema")
            
            # Ensure access_rules table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='access_rules'")
            if not cursor.fetchone():
                print("Creating 'access_rules' table...")
                cursor.execute("""
                    CREATE TABLE access_rules (
                        id INTEGER NOT NULL PRIMARY KEY,
                        employee_id INTEGER NOT NULL,
                        day_of_week INTEGER NOT NULL,
                        start_time TIME NOT NULL,
                        end_time TIME NOT NULL,
                        FOREIGN KEY(employee_id) REFERENCES employees (id) ON DELETE CASCADE
                    )
                """)
                conn.commit()
                print("✓ Created 'access_rules' table")
            
            print("\n✓ Migration completed successfully!")
            
        except Exception as e:
            conn.rollback()
            print(f"✗ Migration failed: {str(e)}")
            raise
        finally:
            conn.close()

if __name__ == '__main__':
    migrate_database()

