import sys
import os
sys.path.append(os.getcwd())

from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    # Check if columns exist and add them if not (for SQLite)
    try:
        db.session.execute(text("ALTER TABLE users ADD COLUMN registration_number VARCHAR(20)"))
        print("Added registration_number to users table")
    except Exception as e:
        print(f"users table: {e}")

    try:
        db.session.execute(text("ALTER TABLE contracts ADD COLUMN user_registration_number_snapshot VARCHAR(20)"))
        print("Added user_registration_number_snapshot to contracts table")
    except Exception as e:
        print(f"contracts table: {e}")

    db.session.commit()
    print("Database update attempt finished.")
