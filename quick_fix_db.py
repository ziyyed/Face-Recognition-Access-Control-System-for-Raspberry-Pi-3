"""
Quick fix for database schema - adds missing 'position' column.

Run this script to immediately fix the database schema issue.
"""

import sqlite3
import os
from pathlib import Path

def quick_fix():
    db_file = "access_control.db"
    
    if not os.path.exists(db_file):
        print(f"❌ Database file '{db_file}' not found.")
        print("   The database will be created automatically when you start the Flask app.")
        return False
    
    print(f"✓ Found database: {db_file}")
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # Check if position column exists
        cursor.execute("PRAGMA table_info(employees)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'position' in columns:
            print("✓ Database already has 'position' column. No fix needed.")
            return True
        
        # Add the column
        print("Adding 'position' column...")
        cursor.execute("ALTER TABLE employees ADD COLUMN position VARCHAR(100)")
        conn.commit()
        
        # Verify
        cursor.execute("PRAGMA table_info(employees)")
        columns_after = [row[1] for row in cursor.fetchall()]
        
        if 'position' in columns_after:
            print("✓ Successfully added 'position' column!")
            print(f"   Columns now: {', '.join(columns_after)}")
            return True
        else:
            print("❌ Failed to add column")
            return False
            
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e).lower():
            print("✓ Column already exists (database was fixed)")
            return True
        else:
            print(f"❌ Error: {e}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 50)
    print("Quick Database Fix")
    print("=" * 50)
    print()
    
    if quick_fix():
        print()
        print("✓ Database fixed! You can now run the Flask app.")
    else:
        print()
        print("❌ Fix failed. Please check the errors above.")
    
    print("=" * 50)

