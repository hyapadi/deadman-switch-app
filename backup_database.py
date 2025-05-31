#!/usr/bin/env python3
"""
Database Backup and Restore Utility
Always run this before making any database changes!
"""
import os
import shutil
import sqlite3
from datetime import datetime
import json

def backup_database():
    """Create a complete backup of the database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Copy the database file
    if os.path.exists("deadman_switch.db"):
        backup_file = f"deadman_switch_backup_{timestamp}.db"
        shutil.copy2("deadman_switch.db", backup_file)
        print(f"✅ Database file backed up to: {backup_file}")
        
        # 2. Export SQL dump
        sql_backup = f"deadman_switch_dump_{timestamp}.sql"
        os.system(f'sqlite3 deadman_switch.db ".dump" > {sql_backup}')
        print(f"✅ SQL dump created: {sql_backup}")
        
        # 3. Export user data as JSON for easy recovery
        export_users_json(timestamp)
        
        return backup_file, sql_backup
    else:
        print("❌ No database file found!")
        return None, None

def export_users_json(timestamp):
    """Export users data as JSON for easy recovery"""
    try:
        conn = sqlite3.connect("deadman_switch.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Export users
        cursor.execute("SELECT * FROM users")
        users = [dict(row) for row in cursor.fetchall()]
        
        # Export switches if table exists
        switches = []
        try:
            cursor.execute("SELECT * FROM deadman_switches")
            switches = [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            pass
        
        # Export check-ins if table exists
        check_ins = []
        try:
            cursor.execute("SELECT * FROM check_ins")
            check_ins = [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            pass
        
        backup_data = {
            "timestamp": timestamp,
            "users": users,
            "deadman_switches": switches,
            "check_ins": check_ins
        }
        
        json_file = f"deadman_switch_data_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        print(f"✅ Data exported to JSON: {json_file}")
        print(f"   - Users: {len(users)}")
        print(f"   - Switches: {len(switches)}")
        print(f"   - Check-ins: {len(check_ins)}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error exporting data: {e}")

def restore_users_from_json(json_file):
    """Restore users from JSON backup"""
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        conn = sqlite3.connect("deadman_switch.db")
        cursor = conn.cursor()
        
        for user in data['users']:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO users 
                    (id, username, email, hashed_password, full_name, role, is_active, is_verified, created_at, updated_at, last_login)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user['id'], user['username'], user['email'], user['hashed_password'],
                    user['full_name'], user['role'], user['is_active'], user['is_verified'],
                    user['created_at'], user['updated_at'], user['last_login']
                ))
                print(f"✅ Restored user: {user['username']}")
            except Exception as e:
                print(f"❌ Error restoring user {user['username']}: {e}")
        
        conn.commit()
        conn.close()
        print("✅ User restoration completed!")
        
    except Exception as e:
        print(f"❌ Error restoring from JSON: {e}")

def list_backups():
    """List all available backups"""
    print("\n📁 Available Backups:")
    
    db_backups = [f for f in os.listdir('.') if f.startswith('deadman_switch_backup_')]
    sql_backups = [f for f in os.listdir('.') if f.startswith('deadman_switch_dump_')]
    json_backups = [f for f in os.listdir('.') if f.startswith('deadman_switch_data_')]
    
    print(f"Database files: {len(db_backups)}")
    for backup in sorted(db_backups):
        print(f"  - {backup}")
    
    print(f"SQL dumps: {len(sql_backups)}")
    for backup in sorted(sql_backups):
        print(f"  - {backup}")
        
    print(f"JSON exports: {len(json_backups)}")
    for backup in sorted(json_backups):
        print(f"  - {backup}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "backup":
            backup_database()
        elif sys.argv[1] == "list":
            list_backups()
        elif sys.argv[1] == "restore" and len(sys.argv) > 2:
            restore_users_from_json(sys.argv[2])
        else:
            print("Usage:")
            print("  python backup_database.py backup")
            print("  python backup_database.py list")
            print("  python backup_database.py restore <json_file>")
    else:
        backup_database()
