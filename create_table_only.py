from app import create_app, db
from app.models.branch import BranchFloor
import traceback

app = create_app()

with app.app_context():
    try:
        print("Attempting to create branch_floors table...")
        BranchFloor.__table__.create(db.engine)
        print("Successfully created branch_floors table")
    except Exception:
        traceback.print_exc()
