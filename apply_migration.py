import os
from app import create_app, db
from sqlalchemy import text

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

def apply_migration():
    with app.app_context():
        with open('migrations/create_branch_floors.sql', 'r') as f:
            sql = f.read()
            # Split by semicolon if there are multiple statements, but here it's one statement
            # However, sqlalchemy execute might not like multiple statements in one go depending on driver
            # The file has one CREATE TABLE statement.
            try:
                with db.engine.connect() as connection:
                    connection.execute(text(sql))
                    connection.commit()
                print("Migration applied successfully.")
            except Exception as e:
                import traceback
                traceback.print_exc()

if __name__ == '__main__':
    apply_migration()
