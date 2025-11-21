"""
Fix database schema - remove face_id column constraint.

This script fixes the issue where the database has a face_id column
that is NOT NULL, but the model doesn't use it.
"""

import sqlite3
import os
from pathlib import Path

def fix_face_id_issue():
    db_file = "access_control.db"
    
    if not os.path.exists(db_file):
        print(f"❌ Database file '{db_file}' not found.")
        return False
    
    print(f"✓ Found database: {db_file}")
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # Check current schema
        cursor.execute("PRAGMA table_info(employees)")
        columns = {row[1]: row for row in cursor.fetchall()}
        
        print("\nCurrent columns:")
        for col_name, col_info in columns.items():
            not_null = "NOT NULL" if col_info[3] else "NULL"
            print(f"   - {col_name} ({col_info[2]}) {not_null}")
        
        # Check if face_id exists and is NOT NULL
        if 'face_id' in columns:
            if columns['face_id'][3] == 1:  # NOT NULL
                print("\n⚠ Found face_id column with NOT NULL constraint.")
                print("   This needs to be removed. Recreating table...")
                
                # Get existing data (excluding face_id)
                cursor.execute("SELECT id, name, created_at FROM employees")
                employees_data = cursor.fetchall()
                print(f"   Found {len(employees_data)} employees to migrate")
                
                # Create backup table
                cursor.execute("DROP TABLE IF EXISTS employees_backup")
                cursor.execute("""
                    CREATE TABLE employees_backup AS 
                    SELECT id, name, created_at FROM employees
                """)
                
                # Drop old table
                cursor.execute("DROP TABLE employees")
                
                # Create new table with correct schema
                cursor.execute("""
                    CREATE TABLE employees (
                        id INTEGER NOT NULL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        position VARCHAR(100),
                        created_at DATETIME
                    )
                """)
                
                # Restore data
                for emp in employees_data:
                    cursor.execute("""
                        INSERT INTO employees (id, name, created_at)
                        VALUES (?, ?, ?)
                    """, emp)
                
                # Drop backup
                cursor.execute("DROP TABLE employees_backup")
                
                conn.commit()
                print("✓ Successfully recreated employees table without face_id")
                
                # Check for position column
                cursor.execute("PRAGMA table_info(employees)")
                columns_after = [row[1] for row in cursor.fetchall()]
                
                if 'position' not in columns_after:
                    print("Adding 'position' column...")
                    cursor.execute("ALTER TABLE employees ADD COLUMN position VARCHAR(100)")
                    conn.commit()
                    print("✓ Added 'position' column")
                
                return True
            else:
                print("✓ face_id column exists but is nullable. No fix needed.")
                return True
        else:
            print("✓ No face_id column found. Schema is correct.")
            
            # Check for position column
            if 'position' not in columns:
                print("Adding 'position' column...")
                cursor.execute("ALTER TABLE employees ADD COLUMN position VARCHAR(100)")
                conn.commit()
                print("✓ Added 'position' column")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Fix face_id Column Issue")
    print("=" * 60)
    print()
    
    if fix_face_id_issue():
        print()
        print("=" * 60)
        print("✓ Database fixed successfully!")
        print("  You can now add employees without errors.")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("❌ Fix failed. Please check the errors above.")
        print("=" * 60)

