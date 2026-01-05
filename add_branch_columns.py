from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    # SQLite ALTER TABLE syntax
    columns = [
        ("operating_hours", "VARCHAR(100)"),
        ("contact", "VARCHAR(50)"),
        ("traffic_info", "TEXT"),
        ("parking_info", "TEXT")
    ]
    
    for col_name, col_type in columns:
        try:
            # Note: We use execute(text(...)) for raw SQL in modern SQLAlchemy
            db.session.execute(text(f"ALTER TABLE branches ADD COLUMN {col_name} {col_type}"))
            print(f"Added column {col_name}")
        except Exception as e:
            # We skip if column already exists (Error message usually contains 'duplicate column name')
            print(f"Could not add column {col_name}: {e}")
    
    db.session.commit()
    print("Migration finished.")
