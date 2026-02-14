from app.extensions import db
from datetime import datetime

class Coupon(db.Model):
    __tablename__ = 'coupons'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    
    # Discount Details
    discount_type = db.Column(db.String(20), nullable=False) # 'percentage', 'fixed'
    discount_value = db.Column(db.Integer, nullable=False)
    discount_cycle = db.Column(db.String(20), default='once') # 'once', 'monthly'
    
    # Stacking Policy
    stack_policy = db.Column(db.String(30), default='STACK_WITH_MONTHLY_PROMO') # 'STACK_WITH_MONTHLY_PROMO', 'EXCLUSIVE'
    
    # Validity
    valid_from = db.Column(db.Date, nullable=False)
    valid_until = db.Column(db.Date, nullable=False)
    
    # Conditions
    min_months = db.Column(db.Integer, nullable=True) # Minimum contract months required
    
    # Usage Limits
    usage_limit = db.Column(db.Integer, nullable=True) # Total max usage count
    used_count = db.Column(db.Integer, default=0)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_valid(self):
        now = datetime.utcnow().date()
        if not self.is_active:
            return False, "비활성화된 쿠폰입니다."
        if now < self.valid_from or now > self.valid_until:
            return False, "유효기간이 지난 쿠폰입니다."
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False, "선착순 마감된 쿠폰입니다."
        return True, "유효한 쿠폰입니다."

    def __repr__(self):
        return f'<Coupon {self.code}>'
