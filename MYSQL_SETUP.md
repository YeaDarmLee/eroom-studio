# MySQL Connection Setup - Verification Guide

## ✅ Changes Made

### 1. Fixed .env Loading
**File**: `run.py`
- Added `load_dotenv()` before app creation
- Ensures environment variables are loaded from `.env` file

### 2. Updated Config
**File**: `config.py`
- Removed SQLite override
- Now properly reads `DATABASE_URL` from environment
- Falls back to SQLite only if `DATABASE_URL` is not set

### 3. Added MySQL Driver
**File**: `requirements.txt`
- Added `mysql-connector-python==8.2.0`
- Package has been installed successfully

### 4. Added Debug Logging
**File**: `app/__init__.py`
- Added console output to show which database URL is being used
- Will print on app startup

## 🔍 Verification Steps

### Step 1: Check .env File
Ensure your `.env` file contains:
```
SECRET_KEY=dev-secret-key
DATABASE_URL=mysql+mysqlconnector://root:dldPekfa1!@localhost:3306/eroom
```

### Step 2: Verify MySQL Database Exists
Run this in MySQL:
```sql
SHOW DATABASES LIKE 'eroom';
```

If it doesn't exist, create it:
```sql
CREATE DATABASE eroom CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Step 3: Test Connection
Run the Flask app:
```bash
python run.py
```

**Expected Output:**
```
================================================================================
>>> DATABASE URL: mysql+mysqlconnector://root:***@localhost:3306/eroom
================================================================================
```

If you see `sqlite:///eroom.db`, the `.env` file is not being loaded correctly.

### Step 4: Run Migrations
Once the connection is verified, run:
```bash
flask db upgrade
```

This will create all tables in the MySQL database.

### Step 5: Verify Tables
Check that tables were created:
```sql
USE eroom;
SHOW TABLES;
```

You should see:
- `users`
- `branches`
- `rooms`
- `contracts`
- `requests`
- `tenant_room_link_requests`
- `alembic_version`

## 🐛 Troubleshooting

### Issue: Still seeing SQLite
**Solution**: 
1. Check that `.env` file is in the project root
2. Verify `DATABASE_URL` is set correctly in `.env`
3. Restart the Flask app completely

### Issue: "Access denied for user 'root'"
**Solution**:
1. Verify MySQL password is correct
2. Check MySQL is running: `mysql -u root -p`
3. Grant permissions if needed:
```sql
GRANT ALL PRIVILEGES ON eroom.* TO 'root'@'localhost';
FLUSH PRIVILEGES;
```

### Issue: "Unknown database 'eroom'"
**Solution**:
```sql
CREATE DATABASE eroom CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Issue: "No module named 'mysql'"
**Solution**:
```bash
pip install mysql-connector-python==8.2.0
```

## 📝 Next Steps

1. **Stop any running Flask instances**
2. **Restart the app**: `python run.py`
3. **Check the console output** for the DATABASE URL
4. **Run migrations**: `flask db upgrade`
5. **Load seed data** (if you have a seed script)
6. **Test the application** with MySQL backend

## 🎯 Success Criteria

- ✅ Console shows MySQL URL on startup
- ✅ `flask db upgrade` completes without errors
- ✅ Tables exist in MySQL database
- ✅ Application can read/write to MySQL
- ✅ Login and admin features work with MySQL data
