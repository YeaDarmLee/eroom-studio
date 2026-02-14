from datetime import datetime
from app.extensions import db
from app.models.contract import Contract

def terminate_expired_contracts(app):
    """오늘 날짜 기준으로 종료일이 지난 활성 계약들을 종료 처리합니다."""
    with app.app_context():
        today = datetime.utcnow().date()
        # Find expired contracts
        expired_contracts = Contract.query.filter(
            Contract.status == 'active',
            Contract.end_date < today
        ).all()
        
        expired_count = len(expired_contracts)
        
        if expired_count > 0:
            for contract in expired_contracts:
                contract.status = 'terminated'
                if contract.room:
                    # 방 상태를 계약 가능 상태로 변경
                    contract.room.status = 'available'
            
            db.session.commit()
            print(f"[{datetime.now()}] Auto-terminated {expired_count} expired contracts and updated room statuses.")
