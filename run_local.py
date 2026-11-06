"""Safe preview: SQLite only, no scheduled jobs, no external SMS delivery."""
from datetime import date, timedelta
from app import create_app
from app.extensions import db
from app.models import Branch, Room, User, Contract
from app.models.coupon import Coupon
from app.models.contract import TermsDocument
from app.models.request import Request

app = create_app('local')

def seed_preview():
    with app.app_context():
        db.create_all()
        if User.query.first():
            return
        admin = User(name='로컬 관리자', email='admin@local.test', role='admin')
        user = User(name='로컬 입주자', email='tenant@local.test', phone='01000000001')
        admin.set_password('Local-preview-123!')
        user.set_password('Local-preview-123!')
        branch = Branch(name='로컬 테스트점', address='테스트 전용 주소', owner_name='로컬 관리자', owner_contact='01000000000')
        db.session.add_all([admin, user, branch])
        db.session.flush()
        room = Room(branch_id=branch.id, name='101', price=500000, deposit=300000, floor='1F', status='occupied')
        db.session.add_all([room,
            Room(branch_id=branch.id, name='102', price=400000, deposit=300000, floor='1F', status='available'),
            Room(branch_id=branch.id, name='시간제', room_type='time_based', price=10000, deposit=0, floor='1F', status='available')])
        db.session.flush()
        contract = Contract(user_id=user.id, room_id=room.id, start_date=date.today()-timedelta(days=30),
                                end_date=date.today()+timedelta(days=90), months=4, price=500000,
                                deposit=300000, status='active', payment_day=1)
        db.session.add(contract)
        db.session.flush()
        db.session.add_all([
            TermsDocument(version='v1', content='로컬 검증용 약관', content_hash='local-preview-only'),
            Coupon(code='LOCAL10K', discount_type='fixed', discount_value=10000, discount_cycle='monthly',
                   valid_from=date.today()-timedelta(days=1), valid_until=date.today()+timedelta(days=365)),
            Request(user_id=user.id, contract_id=contract.id, type='repair', status='submitted', details='{"message":"로컬 테스트 수리 요청"}'),
            Request(user_id=user.id, type='inquiry', status='submitted', details='{"message":"로컬 테스트 문의"}')])
        db.session.commit()

if __name__ == '__main__':
    seed_preview()
    print('LOCAL PREVIEW: isolated SQLite; SMS and scheduler disabled. http://127.0.0.1:5057')
    app.run(host='127.0.0.1', port=5057, use_reloader=False)
