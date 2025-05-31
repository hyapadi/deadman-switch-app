# Development Safety Checklist

## Before Making ANY Database-Related Changes

### ✅ Pre-Change Checklist

1. **Backup Current Data**
   ```bash
   python backup_database.py backup
   ```

2. **Document Current State**
   ```bash
   # Check existing users
   sqlite3 deadman_switch.db "SELECT id, username, email, role FROM users;"
   
   # Check existing switches
   sqlite3 deadman_switch.db "SELECT id, user_id, name, status FROM deadman_switches;"
   
   # Check table structure
   sqlite3 deadman_switch.db ".schema"
   ```

3. **Test Changes on Backup First**
   ```bash
   cp deadman_switch.db test_changes.db
   # Test all changes on test_changes.db first
   ```

### ✅ During Changes

1. **Never use destructive operations on production data**
   - ❌ `Base.metadata.drop_all()`
   - ❌ `Base.metadata.create_all()` on existing DB
   - ✅ Use proper Alembic migrations

2. **Always check data before and after**
   ```bash
   # Before changes
   sqlite3 deadman_switch.db "SELECT COUNT(*) as user_count FROM users;"
   
   # After changes
   sqlite3 deadman_switch.db "SELECT COUNT(*) as user_count FROM users;"
   ```

3. **Use transactions for safety**
   ```python
   async with db.begin():
       # Make changes here
       # Will rollback automatically if error occurs
   ```

### ✅ Post-Change Verification

1. **Verify Data Integrity**
   ```bash
   # Check all users still exist
   sqlite3 deadman_switch.db "SELECT username FROM users;"
   
   # Check application still works
   curl http://localhost:8000/health
   ```

2. **Test Critical Functionality**
   - Login with existing users
   - Create new switch
   - Perform check-in
   - Admin functions

3. **Document Changes Made**
   - What was changed
   - Why it was changed
   - What data was affected

### ✅ Recovery Procedures

If data is lost:

1. **Stop the application immediately**
2. **Restore from backup**
   ```bash
   cp deadman_switch_backup_YYYYMMDD_HHMMSS.db deadman_switch.db
   ```
3. **Or restore from JSON**
   ```bash
   python backup_database.py restore deadman_switch_data_YYYYMMDD_HHMMSS.json
   ```

### ✅ Safe Migration Practices

1. **Always use Alembic for schema changes**
   ```bash
   # Create migration
   uv run alembic revision --autogenerate -m "Description of change"
   
   # Review migration file before applying
   cat alembic/versions/xxx_description.py
   
   # Apply migration
   uv run alembic upgrade head
   ```

2. **Test migrations on backup data**
   ```bash
   cp deadman_switch.db test_migration.db
   # Test migration on test_migration.db first
   ```

## Emergency Contacts

If you lose data and need help:
1. Check backup files first
2. Look for JSON exports
3. Check git history for recent changes
4. Document what was lost for future prevention

## Prevention is Better Than Recovery!

**ALWAYS BACKUP BEFORE CHANGES!**
