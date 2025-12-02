from app import create_app, db
from sqlalchemy import inspect

app = create_app()

with app.app_context():
    try:
        inspector = inspect(db.engine)
        if 'branches' in inspector.get_table_names():
            print("branches table exists")
            columns = inspector.get_columns('branches')
            for col in columns:
                print(f"Column: {col['name']} - {col['type']}")
        else:
            print("branches table does NOT exist")
    except Exception as e:
        print(f"Error: {e}")
