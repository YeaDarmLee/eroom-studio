import os
from app import create_app, db
from sqlalchemy import inspect

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

def list_tables():
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print("Tables:", tables)
        if 'branch_floors' in tables:
            print("branch_floors table exists.")
        else:
            print("branch_floors table MISSING.")

if __name__ == '__main__':
    list_tables()
