import os
from app import create_app, db
from sqlalchemy import inspect, text

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

def inspect_branches():
    with app.app_context():
        with db.engine.connect() as connection:
            result = connection.execute(text("SHOW CREATE TABLE branches"))
            with open('branches_schema.txt', 'w') as f:
                for row in result:
                    f.write(row[1])

if __name__ == '__main__':
    inspect_branches()
