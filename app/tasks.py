from datetime import datetime, timedelta
import pytz
from app.extensions import db
from app.models.contract import Contract

def get_kst_now():
    """한국 표준시(KST) 현재 시각 반환"""
    return datetime.now(pytz.timezone('Asia/Seoul'))

def terminate_expired_contracts(app):
    """오늘 날짜 기준으로 종료일이 지난 활성 계약들을 종료 처리합니다."""
    with app.app_context():
        # KST 기준으로 오늘 날짜 계산
        today = get_kst_now().date()
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
            print(f"[{get_kst_now()}] Auto-terminated {expired_count} expired contracts and updated room statuses.")

def process_daily_sms_tasks(app):
    """결제 안내, 자동 연장 안내 등 매일 오전 9시에 실행되는 일괄 SMS 작업을 처리합니다."""
    from app.utils.sms_service import sms_service
    from app.utils.sms_context import build_sms_context
    
    with app.app_context():
        now_kst = get_kst_now()
        today = now_kst.date()
        
        # 1. PAYMENT_REMINDER
        template = sms_service.get_template('PAYMENT_REMINDER')
        offset = template.schedule_offset if template else -3
        target_payment_date = today - timedelta(days=offset)
        
        reminder_contracts = Contract.query.filter(
            Contract.status == 'active',
            Contract.payment_day == target_payment_date.day
        ).all()
        
        for contract in reminder_contracts:
            context = build_sms_context(contract, 'PAYMENT_REMINDER', due_date=target_payment_date.strftime('%Y-%m-%d'))
            sms_service.send_sms(contract.id, 'PAYMENT_REMINDER', context, related_date=target_payment_date)
 
        # 2. AUTO_RENEW_NOTICE
        template = sms_service.get_template('AUTO_RENEW_NOTICE')
        offset = template.schedule_offset if template else -30
        target_expiry_date = today - timedelta(days=offset)
 
        expiry_contracts = Contract.query.filter(
            Contract.status == 'active',
            Contract.end_date == target_expiry_date,
            Contract.is_indefinite == False
        ).all()
        
        for contract in expiry_contracts:
            context = build_sms_context(contract, 'AUTO_RENEW_NOTICE', renew_deadline=today.strftime('%Y-%m-%d'))
            sms_service.send_sms(contract.id, 'AUTO_RENEW_NOTICE', context, related_date=contract.end_date)
            
        # 3. PAYMENT_OVERDUE_STAGE1
        template = sms_service.get_template('PAYMENT_OVERDUE_STAGE1')
        offset = template.schedule_offset if template else 1
        target_overdue1_date = today - timedelta(days=offset)
 
        overdue1_contracts = Contract.query.filter(
            Contract.status == 'active',
            Contract.payment_day == target_overdue1_date.day
        ).all()
        for contract in overdue1_contracts:
            context = build_sms_context(contract, 'PAYMENT_OVERDUE_STAGE1', due_date=target_overdue1_date.strftime('%Y-%m-%d'))
            sms_service.send_sms(contract.id, 'PAYMENT_OVERDUE_STAGE1', context, related_date=target_overdue1_date)
 
        # 4. PAYMENT_OVERDUE_STAGE2
        template = sms_service.get_template('PAYMENT_OVERDUE_STAGE2')
        offset = template.schedule_offset if template else 5
        target_overdue2_date = today - timedelta(days=offset)
 
        overdue2_contracts = Contract.query.filter(
            Contract.status == 'active',
            Contract.payment_day == target_overdue2_date.day
        ).all()
        for contract in overdue2_contracts:
            context = build_sms_context(contract, 'PAYMENT_OVERDUE_STAGE2', due_date=target_overdue2_date.strftime('%Y-%m-%d'))
            sms_service.send_sms(contract.id, 'PAYMENT_OVERDUE_STAGE2', context, related_date=target_overdue2_date)
 
        # 5. MOVEOUT_DAY
        template = sms_service.get_template('MOVEOUT_DAY')
        offset = template.schedule_offset if template else 0
        target_moveout_date = today - timedelta(days=offset)
 
        moveout_contracts = Contract.query.filter(
            Contract.status == 'active',
            Contract.end_date == target_moveout_date,
            Contract.is_indefinite == False
        ).all()
        for contract in moveout_contracts:
            context = build_sms_context(contract, 'MOVEOUT_DAY')
            sms_service.send_sms(contract.id, 'MOVEOUT_DAY', context, related_date=target_moveout_date)

        print(f"[{now_kst}] Processed daily SMS tasks: Reminder({len(reminder_contracts)}), Expiry({len(expiry_contracts)}), Overdue1({len(overdue1_contracts)}), Overdue2({len(overdue2_contracts)}), MoveoutDay({len(moveout_contracts)})")
