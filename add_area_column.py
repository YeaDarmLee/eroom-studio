from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        # Check if column exists
        db.session.execute(text("SELECT area FROM rooms LIMIT 1"))
        print("Column 'area' already exists.")
    except Exception:
        db.session.rollback()
        print("Adding column 'area' to 'rooms' table...")
        db.session.execute(text("ALTER TABLE rooms ADD COLUMN area FLOAT"))
        db.session.commit()
        print("Column added successfully.")
