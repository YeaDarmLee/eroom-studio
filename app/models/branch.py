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
    
    rooms = db.relationship('Room', backref='branch', lazy='dynamic')
    services = db.relationship('BranchService', backref='branch', lazy='dynamic', cascade='all, delete-orphan')

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

class BranchService(db.Model):
    __tablename__ = 'branch_services'

    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    service_type = db.Column(db.String(20), nullable=False)  # 'common' or 'specialized'
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    icon = db.Column(db.String(50))  # Remix Icon class name (e.g., 'ri-wifi-line')
    order_index = db.Column(db.Integer, default=0)  # For ordering services
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<BranchService {self.name} ({self.service_type})>'

class Room(db.Model):
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    floor = db.Column(db.String(20))  # e.g., "B1", "1F", "2F", "3F"
    name = db.Column(db.String(50), nullable=False) # e.g., "101호"
    description = db.Column(db.Text)
    price = db.Column(db.Integer)
    status = db.Column(db.String(20), default='available') 
    # available, reserved, occupied, maintenance
    
    # Coordinates for floor plan (percentages)
    position_x = db.Column(db.Float, default=0)
    position_y = db.Column(db.Float, default=0)
    width = db.Column(db.Float, default=10)
    height = db.Column(db.Float, default=10)
    
    contracts = db.relationship('Contract', backref='room', lazy='dynamic')

    def __repr__(self):
        return f'<Room {self.name}>'
