from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        print("Repairing branches table...")
        # 1. Alter owner_user_id to be UNSIGNED and match users.id
        try:
            conn.execute(text("ALTER TABLE branches MODIFY COLUMN owner_user_id INTEGER UNSIGNED"))
            print("Successfully modified owner_user_id to UNSIGNED")
        except Exception as e:
            print(f"Error modifying owner_user_id: {e}")

        # 2. Add Foreign Key if it doesn't exist
        try:
            conn.execute(text("ALTER TABLE branches ADD CONSTRAINT fk_branches_owner_user_id FOREIGN KEY (owner_user_id) REFERENCES users (id)"))
            print("Successfully added foreign key fk_branches_owner_user_id")
        except Exception as e:
            print(f"Error adding foreign key: {e}")

        # 3. Drop old columns
        for col in ['contact_info', 'transport_info']:
            try:
                conn.execute(text(f"ALTER TABLE branches DROP COLUMN {col}"))
                print(f"Successfully dropped column {col}")
            except Exception as e:
                print(f"Error dropping column {col}: {e}")
        
        conn.commit()
    print("Repair complete.")
