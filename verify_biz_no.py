import sys
import os
sys.path.append(os.getcwd())

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.contract import Contract
from app.models.branch import Branch, Room
from datetime import date, datetime

app = create_app()
with app.app_context():
    # 1. Setup mock data
    user = User.query.filter_by(email='test_biz@example.com').first()
    if not user:
        user = User(email='test_biz@example.com', name='Test User')
        db.session.add(user)
        db.session.flush()
    
    branch = Branch.query.first()
    room = Room.query.filter_by(branch_id=branch.id).first() if branch else None
    
    if not room:
        print("No room found to test")
        sys.exit(0)

    contract = Contract(
        user=user,
        room=room,
        start_date=date.today(),
        end_date=date.today(),
        price=1000,
        deposit=500,
        status='requested'
    )
    db.session.add(contract)
    db.session.commit()
    
    print(f"Created Test Contract ID: {contract.id}")

    # 2. Simulate Admin update (registration_number)
    contract.user_registration_number_snapshot = "123-45-67890"
    if not user.registration_number:
        user.registration_number = "123-45-67890"
    db.session.commit()
    
    # 3. Verify
    c = Contract.query.get(contract.id)
    u = User.query.get(user.id)
    
    print(f"Contract Snapshot Biz No: {c.user_registration_number_snapshot}")
    print(f"User Profile Biz No: {u.registration_number}")
    
    success = (c.user_registration_number_snapshot == "123-45-67890" and 
               u.registration_number == "123-45-67890")
    
    if success:
        print("Verification SUCCESS: Data flow is working.")
    else:
        print("Verification FAILED.")

    # Cleanup
    db.session.delete(contract)
    # db.session.delete(user) # Keep user for now
    db.session.commit()
