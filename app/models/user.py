from app.extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    kakao_id = db.Column(db.String(64), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), unique=True, nullable=True)  # 계약 매핑 키로 사용
    name = db.Column(db.String(64), nullable=True)
    role = db.Column(db.String(20), default='user')  # user, admin
    onboarding_status = db.Column(db.String(20), default='not_started')
    # not_started, new_user_done, existing_pending, existing_linked
    password_hash = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    contracts = db.relationship('Contract', backref='user', lazy='dynamic')
    requests = db.relationship('Request', backref='user', lazy='dynamic')
    link_requests = db.relationship('TenantRoomLinkRequest', backref='user', lazy='dynamic')

    def set_password(self, password):
        """Hash and set the password"""
        # Use pbkdf2:sha256 instead of scrypt for compatibility with Python 3.9
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """Verify password against hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.name}>'
