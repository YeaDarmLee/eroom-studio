from app.extensions import db
from datetime import datetime

class TenantRoomLinkRequest(db.Model):
    __tablename__ = 'tenant_room_link_requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    branch_name = db.Column(db.String(100)) # User input
    room_name = db.Column(db.String(50))   # User input
    memo = db.Column(db.Text)
    
    status = db.Column(db.String(20), default='pending')
    # pending, approved, rejected
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<LinkRequest {self.user_id} - {self.status}>'
