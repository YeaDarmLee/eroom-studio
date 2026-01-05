from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        # Check if column exists
        db.session.execute(text("SELECT deposit FROM rooms LIMIT 1"))
        print("Column 'deposit' already exists.")
    except Exception:
        db.session.rollback()
        print("Adding column 'deposit' to 'rooms' table...")
        db.session.execute(text("ALTER TABLE rooms ADD COLUMN deposit INTEGER"))
        db.session.commit()
        print("Column added successfully.")
