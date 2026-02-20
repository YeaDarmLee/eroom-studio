from datetime import datetime
import pytz
from app.extensions import db

def get_kst_now():
    """한국 표준시(KST) 현재 시각 반환"""
    return datetime.now(pytz.timezone('Asia/Seoul'))

class SmsTemplate(db.Model):
    __tablename__ = 'sms_templates'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(50), unique=True, nullable=False) # 예: CONTRACT_APPLIED
    title = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    schedule_offset = db.Column(db.Integer, default=0, nullable=False) # 발송 시점 오프셋 (일 단위)
    updated_by_admin_id = db.Column(db.Integer)
    updated_reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=get_kst_now)
    updated_at = db.Column(db.DateTime, default=get_kst_now, onupdate=get_kst_now)

class SmsLog(db.Model):
    __tablename__ = 'sms_logs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id', ondelete='SET NULL'), nullable=True)
    type = db.Column(db.String(50), nullable=False)
    dedup_key = db.Column(db.String(100), unique=True, nullable=False)
    related_date = db.Column(db.Date)
    content_snapshot = db.Column(db.Text, nullable=False)
    context_snapshot = db.Column(db.JSON)
    status = db.Column(db.String(20), nullable=False) # SENT, FAILED, SKIPPED, PENDING
    provider_info = db.Column(db.String(50))
    provider_message_id = db.Column(db.String(100))
    error_message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=get_kst_now)

    contract = db.relationship('Contract', backref=db.backref('sms_logs', lazy=True))
