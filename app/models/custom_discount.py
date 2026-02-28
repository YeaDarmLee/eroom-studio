from sqlalchemy.dialects.mysql import INTEGER
from app.extensions import db
from datetime import datetime
import pytz

def get_kst_now():
    """한국 표준시(KST) 현재 시각 반환"""
    return datetime.now(pytz.timezone('Asia/Seoul'))

class CustomDiscount(db.Model):
    __tablename__ = 'custom_discounts'
    __table_args__ = (
        db.UniqueConstraint('contract_id', 'target_month', name='uix_custom_discount_contract_month'),
    )

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(INTEGER(unsigned=True), db.ForeignKey('contracts.id', ondelete='CASCADE'), nullable=False)
    
    # Target month in YYYY-MM format
    target_month = db.Column(db.String(7), nullable=False)
    
    # Discount amount
    amount = db.Column(db.Integer, nullable=False, default=0)
    
    # Reason for the discount
    reason = db.Column(db.String(255), nullable=True)
    
    # Admin who created/updated this discount
    admin_id = db.Column(INTEGER(unsigned=True), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=get_kst_now)
    updated_at = db.Column(db.DateTime, default=get_kst_now, onupdate=get_kst_now)

    # Note: 'contract' relationship can be defined here or in Contract model via backref

    def __repr__(self):
        return f'<CustomDiscount {self.target_month} : {self.amount} for Contract {self.contract_id}>'
