import os
import shutil
from pathlib import Path
from app import app, db, Employee

DATASET_DIR = Path("dataset")

# Mapping legacy folder names to database names
LEGACY_MAP = {
    "zied": "zied chouk",
    "malak": "malak",
    "hassen": "hassen"
}

def migrate():
    if not DATASET_DIR.exists():
        print("Dataset directory not found.")
        return

    with app.app_context():
        for user_dir in DATASET_DIR.iterdir():
            if not user_dir.is_dir():
                continue
            
            # Skip already migrated folders
            if user_dir.name.startswith("User."):
                print(f"Skipping {user_dir.name} (already migrated)")
                continue
            
            folder_name = user_dir.name
            db_name = LEGACY_MAP.get(folder_name, folder_name)
            
            print(f"Processing legacy folder: {folder_name} -> DB Name: {db_name}")
            
            # Find or create employee
            employee = Employee.query.filter_by(name=db_name).first()
            if not employee:
                print(f"  Creating new employee: {db_name}")
                employee = Employee(name=db_name, position="Employee")
                db.session.add(employee)
                db.session.commit()
            else:
                print(f"  Found existing employee: {db_name} (ID: {employee.id})")
            
            # Target directory
            new_dir_name = f"User.{employee.id}"
            new_dir = DATASET_DIR / new_dir_name
            
            # Move/Merge
            if new_dir.exists():
                print(f"  Target directory {new_dir_name} exists. Merging...")
                for img in user_dir.glob("*.jpg"):
                    shutil.move(str(img), str(new_dir / img.name))
                # Remove empty legacy dir
                try:
                    user_dir.rmdir()
                    print(f"  Removed empty legacy dir: {user_dir}")
                except OSError:
                    print(f"  Warning: Could not remove {user_dir} (not empty?)")
            else:
                print(f"  Renaming {user_dir.name} -> {new_dir_name}")
                user_dir.rename(new_dir)
            
            # Standardize filenames in target dir
            print(f"  Standardizing filenames in {new_dir_name}...")
            for i, img_path in enumerate(sorted(new_dir.glob("*.jpg"))):
                new_filename = f"User.{employee.id}.{i+1}.jpg"
                new_img_path = new_dir / new_filename
                if img_path != new_img_path:
                    img_path.rename(new_img_path)
            
            print(f"  Done with {db_name}")

if __name__ == "__main__":
    migrate()
