"""
Force fix database schema - adds missing 'position' column.

This script will:
1. Find the database file (access_control.db)
2. Check if 'position' column exists
3. Add it if missing
4. Verify the fix

Run this if you get: "no such column: employees.position"
"""

import sqlite3
import os
from pathlib import Path

def force_fix_database():
    """Force fix the database schema."""
    db_path = Path("access_control.db")
    
    if not db_path.exists():
        print("❌ Database file 'access_control.db' not found in current directory.")
        print("   The database might be in a different location.")
        print("   Please check where Flask is creating the database file.")
        return False
    
    print(f"✓ Found database: {db_path}")
    print(f"   Size: {db_path.stat().st_size} bytes")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if employees table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employees'")
        if not cursor.fetchone():
            print("❌ 'employees' table doesn't exist!")
            print("   Creating new database with correct schema...")
            conn.close()
            
            # Import app to create database
            from app import app, db
            with app.app_context():
                db.drop_all()
                db.create_all()
            print("✓ New database created with correct schema")
            return True
        
        # Get current columns
        cursor.execute("PRAGMA table_info(employees)")
        columns_info = cursor.fetchall()
        columns = [row[1] for row in columns_info]
        
        print(f"\nCurrent columns in 'employees' table:")
        for col_info in columns_info:
            print(f"   - {col_info[1]} ({col_info[2]})")
        
        if 'position' in columns:
            print("\n✓ 'position' column already exists. Database is up to date!")
            return True
        
        # Add position column
        print(f"\n⚠ Missing 'position' column. Adding it now...")
        cursor.execute("ALTER TABLE employees ADD COLUMN position VARCHAR(100)")
        conn.commit()
        
        # Verify
        cursor.execute("PRAGMA table_info(employees)")
        columns_after = [row[1] for row in cursor.fetchall()]
        
        if 'position' in columns_after:
            print("✓ Successfully added 'position' column!")
            print(f"\nUpdated columns:")
            for col in columns_after:
                print(f"   - {col}")
            return True
        else:
            print("❌ Failed to add 'position' column!")
            return False
        
    except sqlite3.OperationalError as e:
        print(f"❌ SQL Error: {str(e)}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Database Schema Fix Script")
    print("=" * 60)
    print()
    
    success = force_fix_database()
    
    print()
    print("=" * 60)
    if success:
        print("✓ Database fix completed successfully!")
        print("  You can now run the Flask app: python app.py")
    else:
        print("❌ Database fix failed. Please check the errors above.")
    print("=" * 60)

