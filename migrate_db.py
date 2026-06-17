# migrate_db.py
import sqlite3
import os

def migrate_database():
    db_path = 'placement_portal.db'
    
    # Check if database exists
    if not os.path.exists(db_path):
        print("Database doesn't exist. Run app.py first to create it.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get existing columns in users table
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add missing columns
    new_columns = {
        'full_name': 'TEXT',
        'phone': 'TEXT',
        'college': 'TEXT',
        'course': 'TEXT',
        'graduation_year': 'TEXT',
        'bio': 'TEXT',
        'skills': 'TEXT',
        'experience': 'TEXT',
        'education': 'TEXT',
        'resume_path': 'TEXT',
        'profile_pic': 'TEXT'
    }
    
    for col_name, col_type in new_columns.items():
        if col_name not in columns:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                print(f"Added column: {col_name}")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")
    
    conn.commit()
    conn.close()
    print("Migration completed successfully!")

if __name__ == '__main__':
    migrate_database()