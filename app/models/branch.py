from app.extensions import db
from datetime import datetime

class Branch(db.Model):
    __tablename__ = 'branches'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.String(200))
    map_info = db.Column(db.Text) # JSON or specific format
    facilities = db.Column(db.Text) # JSON list of facilities
    image_url = db.Column(db.String(255)) # URL to uploaded image
    operating_hours = db.Column(db.String(100)) # e.g. "24시간"
    contact = db.Column(db.String(50)) # e.g. "032-123-4567"
    traffic_info = db.Column(db.Text) # Traffic details
    parking_info = db.Column(db.Text) # Parking details

    # Owner Info for Contracts
    owner_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # ID of the user who owns the branch
    is_corporate = db.Column(db.Boolean, default=False)
    registration_number = db.Column(db.String(50)) # Business or Corporate Registration Number
    owner_name = db.Column(db.String(64), default='김훈태')
    owner_address = db.Column(db.String(255))
    owner_birth_date = db.Column(db.String(20))
    owner_contact = db.Column(db.String(50), default='010-9488-5093')
    owner_seal_image = db.Column(db.String(255)) # URL or path to seal image
    
    rooms = db.relationship('Room', backref='branch', lazy='dynamic')

    images = db.relationship('BranchImage', backref='branch', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Branch {self.name}>'

class BranchFloor(db.Model):
    __tablename__ = 'branch_floors'

    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    floor = db.Column(db.String(20), nullable=False)
    floor_plan_image = db.Column(db.String(255))
    
    branch = db.relationship('Branch', backref=db.backref('floors', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('branch_id', 'floor', name='unique_branch_floor'),
    )



class Room(db.Model):
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    floor = db.Column(db.String(20))  # e.g., "B1", "1F", "2F", "3F"
    name = db.Column(db.String(50), nullable=False) # e.g., "101호"
    description = db.Column(db.Text)
    room_type = db.Column(db.String(20), default='monthly') # monthly, time_based, manager
    price = db.Column(db.Integer)
    deposit = db.Column(db.Integer) # Security deposit
    area = db.Column(db.Float) # Room area in square meters
    status = db.Column(db.String(20), default='available') 
    # available, reserved, occupied, maintenance
    
    # Coordinates for floor plan (percentages)
    position_x = db.Column(db.Float, default=0)
    position_y = db.Column(db.Float, default=0)
    width = db.Column(db.Float, default=10)
    height = db.Column(db.Float, default=10)
    
    contracts = db.relationship('Contract', backref='room', lazy='dynamic')
    images = db.relationship('RoomImage', backref='room', lazy='dynamic', cascade='all, delete-orphan')

    def get_next_available_date(self):
        """
        Calculates the next available date for this room.
        Returns a date object or None if not bookable.
        """
        if self.room_type == 'manager':
            return None
            
        if self.status == 'available':
            from datetime import date
            return date.today()
            
        if self.status == 'occupied':
            # Check for active contract
            from app.models.contract import Contract
            from datetime import date, timedelta
            active_contract = self.contracts.filter(
                Contract.status.in_(['active', 'waiting_signature', 'approved', 'requested'])
            ).order_by(Contract.end_date.desc()).first()
            
            if active_contract:
                # 1. termination_effective_date has absolute priority (explicit signal)
                if active_contract.termination_effective_date:
                    return active_contract.termination_effective_date + timedelta(days=1)
                
                # 2. automatic expiration for fixed-term contracts (is_indefinite=False)
                # Matches admin UI "Expiring Soon" logic (within 30 days)
                if not active_contract.is_indefinite and active_contract.end_date:
                    today = date.today()
                    diff = active_contract.end_date - today
                    if 0 <= diff.days <= 30:
                        return active_contract.end_date + timedelta(days=1)
        
        return None

    def __repr__(self):
        return f'<Room {self.name}>'

class RoomImage(db.Model):
    __tablename__ = 'room_images'

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<RoomImage {self.id} for Room {self.room_id}>'

class BranchImage(db.Model):
    __tablename__ = 'branch_images'

    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<BranchImage {self.id} for Branch {self.branch_id}>'
