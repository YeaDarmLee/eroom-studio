from app import create_app
from app.extensions import db
from sqlalchemy import inspect

app = create_app()
with app.app_context():
    inspector = inspect(db.engine)
    columns = inspector.get_columns('users')
    for col in columns:
        if col['name'] == 'id':
            print(f"Full info for users.id: {col}")
