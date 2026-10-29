from app.extensions import db
from datetime import datetime

class TermsDocument(db.Model):
    __tablename__ = 'terms_documents'

    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(50), nullable=False, unique=True)
    content = db.Column(db.Text, nullable=False)
    content_hash = db.Column(db.String(64), nullable=False)
    published_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<TermsDocument {self.version}>'

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
    
    # New Fields for Payment
    payment_method = db.Column(db.String(20), default='bank') # bank, card
    payment_day = db.Column(db.Integer, default=1) # 1, 15
    paid_months = db.Column(db.JSON, default=list) # e.g. ["2026-07", "2026-08"]
    
    # Coupon & Discount
    coupon_id = db.Column(db.Integer, db.ForeignKey('coupons.id'), nullable=True)
    coupon = db.relationship('Coupon', backref='contracts')
    discount_details = db.Column(db.Text, nullable=True) # JSON stored as Text for SQLite compatibility
    
    is_indefinite = db.Column(db.Boolean, default=False) # True: "한달 전 통보" (No fixed end date)
    
    status = db.Column(db.String(20), default='requested')
    # requested, waiting_signature, signature_rejected, approved, active, extend_requested, terminate_requested, terminated, cancelled
    
    auto_extend_status = db.Column(db.String(20), default='none')
    # none, notified, will_terminate, extended
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # --- Evidence Fields ---
    terms_document_id = db.Column(db.Integer, db.ForeignKey('terms_documents.id'), nullable=True)
    terms_version = db.Column(db.String(50))
    terms_snapshot_hash = db.Column(db.String(64))
    consented_at = db.Column(db.DateTime)
    consent_ip = db.Column(db.String(45))
    consent_user_agent = db.Column(db.Text)
    consent_method = db.Column(db.String(50))
    tax_invoice_requested = db.Column(db.Boolean, default=False) # 세금계산서 신청 여부

    # Pricing & Penalty
    pricing_snapshot = db.Column(db.JSON)
    penalty_formula_version = db.Column(db.String(50))
    penalty_rule_text = db.Column(db.Text)

    # Notice & PDF
    contract_email_snapshot = db.Column(db.String(120))
    contract_notice_sent_at = db.Column(db.DateTime)
    notice_email_to = db.Column(db.String(120))
    notice_email_attempts = db.Column(db.Integer, default=0)
    notice_last_error = db.Column(db.Text)
    contract_pdf_hash = db.Column(db.String(64))

    # --- Electronic Signature Fields ---
    user_address_snapshot = db.Column(db.String(255))
    user_birth_date_snapshot = db.Column(db.String(20))
    user_registration_number_snapshot = db.Column(db.String(20)) # 사업자등록번호 스냅샷
    signature_data = db.Column(db.Text) # Base64 encoded signature image
    signed_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)

    # Termination
    termination_requested_at = db.Column(db.DateTime)
    termination_effective_date = db.Column(db.Date)
    remaining_months_at_termination = db.Column(db.Integer)
    penalty_amount_snapshot = db.Column(db.JSON)
    termination_confirmation_checked = db.Column(db.Boolean, default=False)
    termination_confirmation_text_snapshot = db.Column(db.Text)

    requests = db.relationship('Request', backref='contract', lazy='dynamic')
    status_history = db.relationship('ContractStatusHistory', backref='contract', lazy='dynamic')
    custom_discounts = db.relationship('CustomDiscount', backref='contract_ref', lazy='dynamic', cascade='all, delete-orphan')

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
                'phone': self.user.phone,
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

    def apply_termination_request(self, termination_date, confirmation_checked=False):
        """해지 신청 처리 (단일 트랜잭션 플로우)"""
        from datetime import datetime
        self.termination_requested_at = datetime.utcnow()
        self.termination_confirmation_checked = confirmation_checked
        self.status = 'terminate_requested'
        if termination_date:
            if isinstance(termination_date, str):
                self.termination_effective_date = datetime.strptime(termination_date, '%Y-%m-%d').date()
            else:
                self.termination_effective_date = termination_date
        if self.room:
            self.room.sync_status()

    def cancel_termination(self):
        """해지 신청 취소/철회/반려 처리 (단일 트랜잭션 플로우)"""
        self.status = 'active'
        self.termination_effective_date = None
        self.termination_requested_at = None
        self.remaining_months_at_termination = None
        self.penalty_amount_snapshot = None
        self.termination_confirmation_text_snapshot = None
        if self.auto_extend_status == 'will_terminate':
            self.auto_extend_status = 'none'
        if self.room:
            self.room.sync_status()

    def approve_termination(self, termination_date=None, immediate=False):
        """해지 신청 승인 처리 (미래 해지 vs 즉시 종료 분기 처리)"""
        from datetime import datetime
        from datetime import timezone, timedelta
        today = datetime.now(timezone(timedelta(hours=9))).date()
        target_date = termination_date or self.termination_effective_date or self.end_date
        
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()

        if immediate or (target_date and target_date < today):
            self.status = 'terminated'
            self.end_date = today if immediate else target_date
            self.termination_effective_date = self.end_date
        else:
            self.status = 'active'
            self.auto_extend_status = 'will_terminate'
            if target_date:
                self.end_date = target_date
                self.termination_effective_date = target_date

        if self.room:
            self.room.sync_status()

    def __repr__(self):
        return f'<Contract {self.id} - {self.status}>'

class ContractStatusHistory(db.Model):
    __tablename__ = 'contract_status_history'

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), nullable=False)
    old_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20), nullable=False)
    actor_id = db.Column(db.Integer)
    actor_type = db.Column(db.String(10)) # 'admin', 'user', 'system'
    actor_ip = db.Column(db.String(45))
    actor_user_agent = db.Column(db.Text)
    source = db.Column(db.String(20)) # 'admin_ui', 'public_api', 'batch'
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    reason = db.Column(db.Text)

    def __repr__(self):
        return f'<StatusHistory {self.contract_id}: {self.old_status} -> {self.new_status}>'

