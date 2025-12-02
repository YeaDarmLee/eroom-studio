from app.extensions import db
from datetime import datetime

class Contract(db.Model):
    __tablename__ = 'contracts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    months = db.Column(db.Integer)
    total_price = db.Column(db.Integer)
    
    status = db.Column(db.String(20), default='requested')
    # requested, approved, active, extend_requested, terminate_requested, terminated, cancelled
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    requests = db.relationship('Request', backref='contract', lazy='dynamic')

    def __repr__(self):
        return f'<Contract {self.id} - {self.status}>'
