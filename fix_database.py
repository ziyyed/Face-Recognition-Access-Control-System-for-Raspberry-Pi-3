"""
Quick fix script to add missing 'position' column to employees table.

Run this script if you get: "no such column: employees.position"
"""

import sqlite3
import os
from pathlib import Path

def fix_database():
    """Add position column if it doesn't exist."""
    db_path = Path("access_control.db")
    
    if not db_path.exists():
        print("Database file not found. Creating new database...")
        # Import app to create database with correct schema
        from app import app, db
        with app.app_context():
            db.create_all()
        print("✓ New database created with correct schema")
        return
    
    print(f"Fixing database: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if employees table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employees'")
        if not cursor.fetchone():
            print("Employees table doesn't exist. Creating all tables...")
            conn.close()
            from app import app, db
            with app.app_context():
                db.create_all()
            print("✓ All tables created")
            return
        
        # Check current columns
        cursor.execute("PRAGMA table_info(employees)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Current columns: {columns}")
        
        if 'position' not in columns:
            print("Adding 'position' column...")
            cursor.execute("ALTER TABLE employees ADD COLUMN position VARCHAR(100)")
            conn.commit()
            print("✓ Successfully added 'position' column")
        else:
            print("✓ 'position' column already exists")
        
        # Verify
        cursor.execute("PRAGMA table_info(employees)")
        columns_after = [row[1] for row in cursor.fetchall()]
        print(f"Columns after fix: {columns_after}")
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    fix_database()
    print("\n✓ Database fix complete! You can now run the Flask app.")

