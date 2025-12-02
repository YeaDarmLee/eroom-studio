"""
Retry migration script
"""
from app import create_app, db
from sqlalchemy import text

def run_migration():
    app = create_app()
    with app.app_context():
        try:
            # Create table
            print("Creating branch_floors table...")
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS branch_floors (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    branch_id INT NOT NULL,
                    floor VARCHAR(20) NOT NULL,
                    floor_plan_image VARCHAR(255),
                    FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE CASCADE
                )
            """))
            
            # Add unique constraint separately to handle potential existence
            try:
                db.session.execute(text("ALTER TABLE branch_floors ADD UNIQUE KEY unique_branch_floor (branch_id, floor)"))
            except Exception:
                print("Unique key might already exist, skipping.")

            # Add columns to rooms
            cols = ['position_x', 'position_y', 'width', 'height']
            for col in cols:
                try:
                    db.session.execute(text(f"ALTER TABLE rooms ADD COLUMN {col} FLOAT DEFAULT 0"))
                    print(f"Added {col}")
                except Exception:
                    print(f"Column {col} might already exist, skipping.")
            
            db.session.commit()
            print("Done.")
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()

if __name__ == '__main__':
    run_migration()
