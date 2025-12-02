from app.extensions import db
from datetime import datetime

class Request(db.Model):
    __tablename__ = 'requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), nullable=True) # Optional for some requests?
    
    type = db.Column(db.String(20), nullable=False) 
    # repair, supplies, extension, termination
    
    status = db.Column(db.String(20), default='submitted')
    # submitted, processing, done
    
    details = db.Column(db.Text) # JSON field for specific details (repair item, qty, etc.)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Request {self.type} - {self.status}>'
