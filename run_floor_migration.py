"""
Database migration script to add floor column to rooms table
"""
from app import create_app, db
from sqlalchemy import text

def run_migration():
    app = create_app()
    
    with app.app_context():
        try:
            # Read migration SQL
            with open('migrations/add_floor_to_rooms.sql', 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--') and not s.strip().startswith('SELECT')]
            
            for statement in statements:
                if statement:
                    print(f"Executing: {statement[:100]}...")
                    db.session.execute(text(statement))
            
            db.session.commit()
            print("\n✅ Migration completed successfully!")
            print("Floor column has been added to rooms table.")
            
            # Verify the change
            result = db.session.execute(text(
                "SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE "
                "FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() "
                "AND TABLE_NAME = 'rooms' "
                "AND COLUMN_NAME = 'floor'"
            ))
            
            row = result.fetchone()
            if row:
                print(f"\n✅ Verification: floor column exists")
                print(f"   Type: {row[1]}")
                print(f"   Nullable: {row[2]}")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Migration failed: {str(e)}")
            raise

if __name__ == '__main__':
    run_migration()
