from app.extensions import db
from datetime import datetime

class Contract(db.Model):
    __tablename__ = 'contracts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 미매핑 계약 허용
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    
    # 미매핑 계약을 위한 임시 사용자 정보 (회원가입 전)
    temp_user_name = db.Column(db.String(64), nullable=True)
    temp_user_phone = db.Column(db.String(20), nullable=True)  # 매핑 키로 사용
    temp_user_email = db.Column(db.String(120), nullable=True)
    
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(10), nullable=True) # For time_based rooms
    end_time = db.Column(db.String(10), nullable=True)   # For time_based rooms
    months = db.Column(db.Integer)
    price = db.Column(db.Integer)  # Monthly rent
    deposit = db.Column(db.Integer) # Deposit
    
    status = db.Column(db.String(20), default='requested')
    # requested, approved, active, extend_requested, terminate_requested, terminated, cancelled
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    requests = db.relationship('Request', backref='contract', lazy='dynamic')

    @property
    def is_unmapped(self):
        """계약이 아직 사용자와 매핑되지 않았는지 확인"""
        return self.user_id is None
    
    def get_user_info(self):
        """사용자 정보 반환 (매핑된 경우 User 정보, 미매핑인 경우 temp 정보)"""
        if self.user_id:
            return {
                'id': self.user.id,
                'name': self.user.name,
                'email': self.user.email,
                'phone': None,  # User 모델에 phone이 없는 경우
                'is_mapped': True
            }
        else:
            return {
                'id': None,
                'name': self.temp_user_name,
                'email': self.temp_user_email,
                'phone': self.temp_user_phone,
                'is_mapped': False
            }

    def __repr__(self):
        return f'<Contract {self.id} - {self.status}>'

