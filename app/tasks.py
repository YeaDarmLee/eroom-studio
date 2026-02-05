from datetime import datetime
from app.extensions import db
from app.models.contract import Contract

def terminate_expired_contracts(app):
    """오늘 날짜 기준으로 종료일이 지난 활성 계약들을 종료 처리합니다."""
    with app.app_context():
        today = datetime.utcnow().date()
        expired_count = Contract.query.filter(
            Contract.status == 'active',
            Contract.end_date < today
        ).update({Contract.status: 'terminated'}, synchronize_session=False)
        
        if expired_count > 0:
            db.session.commit()
            print(f"[{datetime.now()}] Auto-terminated {expired_count} expired contracts.")
