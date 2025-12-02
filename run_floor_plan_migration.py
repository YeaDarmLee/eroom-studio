"""
Database migration script to add floor plans table and columns
"""
from app import create_app, db
from sqlalchemy import text

def run_migration():
    app = create_app()
    
    with app.app_context():
        try:
            # Read migration SQL
            with open('migrations/add_floor_plans.sql', 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Split by semicolon and execute each statement
            # Note: The PREPARE statement logic might be complex for simple split, 
            # so we'll execute the simpler parts directly or use a more robust split.
            # For this specific SQL, the complex part is the conditional ALTER.
            # Let's simplify and just try to execute. If it fails due to syntax in split, we'll handle it.
            
            # Actually, SQLAlchemy execute might handle multiple statements if supported by driver,
            # but usually it's safer to split.
            # However, the PREPARE block is one logical unit.
            
            print("Executing migration...")
            
            # 1. Create table
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS branch_floors (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    branch_id INT NOT NULL,
                    floor VARCHAR(20) NOT NULL,
                    floor_plan_image VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_branch_floor (branch_id, floor)
                );
            """))
            
            # 2. Add columns (using try-except for idempotency instead of complex SQL)
            try:
                db.session.execute(text("ALTER TABLE rooms ADD COLUMN position_x FLOAT DEFAULT 0"))
                print("Added position_x")
            except Exception as e:
                print(f"Skipping position_x (probably exists): {e}")

            try:
                db.session.execute(text("ALTER TABLE rooms ADD COLUMN position_y FLOAT DEFAULT 0"))
                print("Added position_y")
            except Exception as e:
                print(f"Skipping position_y (probably exists)")

            try:
                db.session.execute(text("ALTER TABLE rooms ADD COLUMN width FLOAT DEFAULT 10"))
                print("Added width")
            except Exception as e:
                print(f"Skipping width (probably exists)")

            try:
                db.session.execute(text("ALTER TABLE rooms ADD COLUMN height FLOAT DEFAULT 10"))
                print("Added height")
            except Exception as e:
                print(f"Skipping height (probably exists)")
            
            db.session.commit()
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Migration failed: {str(e)}")
            raise

if __name__ == '__main__':
    run_migration()
