import os
import sys
from app import create_app, db
from sqlalchemy import text

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

def debug_migration():
    with open('migration_error.log', 'w') as log:
        try:
            with app.app_context():
                with db.engine.connect() as connection:
                    print("Connected to DB.", file=log)
                    sql = text("SELECT 1")
                    result = connection.execute(sql)
                    print(f"Select 1 result: {result.scalar()}", file=log)
                    
                    with open('migrations/create_branch_floors.sql', 'r') as f:
                        sql_content = f.read()
                        print(f"SQL Content: {sql_content}", file=log)
                        connection.execute(text(sql_content))
                        connection.commit()
                        print("Migration applied successfully.", file=log)
        except Exception as e:
            import traceback
            traceback.print_exc(file=log)

if __name__ == '__main__':
    debug_migration()
