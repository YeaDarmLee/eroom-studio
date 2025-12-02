from app import create_app, db
# Import models to ensure they are registered with SQLAlchemy
from app.models.branch import Branch, BranchFloor, Room
from app.models.user import User
from app.models.contract import Contract
from app.models.request import Request

app = create_app()

with app.app_context():
    try:
        print("Creating all missing tables...")
        db.create_all()
        print("Successfully ran db.create_all()")
        
        # Verify
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if 'branch_floors' in inspector.get_table_names():
            print("Verified: branch_floors table exists.")
        else:
            print("Error: branch_floors table still NOT found.")
            
    except Exception as e:
        print(f"Error: {e}")
