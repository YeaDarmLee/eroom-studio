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
        from app.models.contract import ContractStatusHistory
        # KST 기준으로 오늘 날짜 계산
        today = get_kst_now().date()
        # Find expired contracts (Active or Termination requested)
        expired_contracts = Contract.query.filter(
            Contract.status.in_(['active', 'terminate_requested']),
            Contract.end_date < today
        ).all()
        
        expired_count = len(expired_contracts)
        
        if expired_count > 0:
            for contract in expired_contracts:
                # will_terminate(퇴실 확정)와 일반 만료를 사유로 구분
                reason = (
                    '관리자 퇴실 확정 후 만료일 경과 자동 종료'
                    if contract.auto_extend_status == 'will_terminate'
                    else '만료일 경과로 인한 자동 종료'
                )
                history = ContractStatusHistory(
                    contract_id=contract.id,
                    old_status=contract.status,
                    new_status='terminated',
                    actor_type='system',
                    source='batch',
                    reason=reason
                )
                db.session.add(history)
                contract.status = 'terminated'
                if contract.room:
                    # 방 상태를 계약 가능 상태로 변경
                    contract.room.status = 'available'
            
            db.session.commit()
            print(f"[{get_kst_now()}] Auto-terminated {expired_count} expired contracts and updated room statuses.")

        # 미체결 상태(서명대기/승인대기/서명거절)에서 계약 종료일 경과한 건 자동 취소 처리
        expired_waiting_contracts = Contract.query.filter(
            Contract.status.in_(['waiting_signature', 'requested', 'signature_rejected']),
            Contract.end_date < today
        ).all()
        
        expired_waiting_count = len(expired_waiting_contracts)
        
        if expired_waiting_count > 0:
            for contract in expired_waiting_contracts:
                reason = '미체결 상태(서명대기/승인대기/서명거절)에서 계약 종료일 경과로 인한 자동 취소'
                history = ContractStatusHistory(
                    contract_id=contract.id,
                    old_status=contract.status,
                    new_status='cancelled',
                    actor_type='system',
                    source='batch',
                    reason=reason
                )
                db.session.add(history)
                contract.status = 'cancelled'
                if contract.room:
                    # 방 상태를 계약 가능 상태로 변경
                    contract.room.status = 'available'
            
            db.session.commit()
            print(f"[{get_kst_now()}] Auto-cancelled {expired_waiting_count} expired waiting contracts and updated room statuses.")


def process_daily_sms_tasks(app):
    """결제 안내, 자동 연장 안내 등 매일 오전 9시에 실행되는 일괄 SMS 작업을 처리합니다."""
    from app.utils.sms_service import sms_service
    from app.utils.sms_context import build_sms_context
    
    with app.app_context():
        now_kst = get_kst_now()
        today = now_kst.date()
        
        # 1. PAYMENT_REMINDER
        template = sms_service.get_template('PAYMENT_REMINDER')
        offset = template.schedule_offset if template else 0
        target_payment_date = today - timedelta(days=offset)
        
        reminder_contracts = Contract.query.filter(
            Contract.status == 'active',
            Contract.payment_day == target_payment_date.day
        ).all()
        
        target_reminder_month_str = target_payment_date.strftime('%Y-%m')
        for contract in reminder_contracts:
            paid_list = contract.paid_months or []
            if target_reminder_month_str in paid_list:
                continue  # 이미 납부 완료된 달 → 발송 건너뜀
            context = build_sms_context(contract, 'PAYMENT_REMINDER', due_date=target_payment_date.strftime('%Y-%m-%d'))
            sms_service.send_sms(contract.id, 'PAYMENT_REMINDER', context, related_date=target_payment_date)
 
        # 2. AUTO_RENEW_NOTICE (30일 전 연장 예정 알림 + 자동연장 대기 상태 전환)
        template = sms_service.get_template('AUTO_RENEW_NOTICE')
        offset = template.schedule_offset if template else -30
        target_expiry_date = today - timedelta(days=offset)
 
        expiry_contracts = Contract.query.filter(
            Contract.status == 'active',
            Contract.end_date <= target_expiry_date,  # == → <= : 배치 누락시에도 처리
            Contract.is_indefinite == False,
            db.or_(Contract.auto_extend_status.in_(['none']), Contract.auto_extend_status.is_(None))
        ).all()
        
        for contract in expiry_contracts:
            context = build_sms_context(contract, 'AUTO_RENEW_NOTICE', renew_deadline=today.strftime('%Y-%m-%d'))
            success, msg = sms_service.send_sms(contract.id, 'AUTO_RENEW_NOTICE', context, related_date=contract.end_date)
            if success:
                # 발송 성공 시 자동연장 대기 상태로 전환
                contract.auto_extend_status = 'notified'
        
        # 보정: 계약 연장 등으로 만료일이 30일 초과로 늘어난 경우 notified -> none 초기화
        mismatched_contracts = Contract.query.filter(
            Contract.status == 'active',
            Contract.auto_extend_status == 'notified',
            Contract.end_date > today + timedelta(days=30),
            Contract.is_indefinite == False
        ).all()
        for mc in mismatched_contracts:
            mc.auto_extend_status = 'none'

        db.session.commit()
            
        # 3. PAYMENT_OVERDUE_STAGE1 (5 days after)
        template = sms_service.get_template('PAYMENT_OVERDUE_STAGE1')
        offset = template.schedule_offset if template else 5
        target_overdue1_date = today - timedelta(days=offset)
        
        overdue1_contracts = Contract.query.filter(
            Contract.status == 'active',
            Contract.payment_day == target_overdue1_date.day
        ).all()
        
        target_month_str = target_overdue1_date.strftime('%Y-%m')
        
        for contract in overdue1_contracts:
            paid_list = contract.paid_months or []
            if target_month_str not in paid_list:
                context = build_sms_context(contract, 'PAYMENT_OVERDUE_STAGE1', due_date=target_overdue1_date.strftime('%Y-%m-%d'))
                sms_service.send_sms(contract.id, 'PAYMENT_OVERDUE_STAGE1', context, related_date=target_overdue1_date)
 
        # 4. PAYMENT_OVERDUE_STAGE2 (Disabled: Manual sending only)
        # template = sms_service.get_template('PAYMENT_OVERDUE_STAGE2')
        # offset = template.schedule_offset if template else 5
        # target_overdue2_date = today - timedelta(days=offset)
        # 
        # overdue2_contracts = Contract.query.filter(
        #     Contract.status == 'active',
        #     Contract.payment_day == target_overdue2_date.day
        # ).all()
        # for contract in overdue2_contracts:
        #     context = build_sms_context(contract, 'PAYMENT_OVERDUE_STAGE2', due_date=target_overdue2_date.strftime('%Y-%m-%d'))
        #     sms_service.send_sms(contract.id, 'PAYMENT_OVERDUE_STAGE2', context, related_date=target_overdue2_date)
 
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

        # 6. WELCOME_MESSAGE (On start_date)
        template = sms_service.get_template('WELCOME_MESSAGE')
        offset = template.schedule_offset if template else 0
        target_start_date = today - timedelta(days=offset)

        welcome_contracts = Contract.query.filter(
            Contract.status == 'active',
            Contract.start_date == target_start_date
        ).all()
        for contract in welcome_contracts:
            context = build_sms_context(contract, 'WELCOME_MESSAGE')
            sms_service.send_sms(contract.id, 'WELCOME_MESSAGE', context, related_date=target_start_date)

        # 7. AUTO_EXTEND_PROCESS (7일 대기 후 연장 처리, 즉 만료 23일 전 실행)
        # notified(30일 전 알림 수신) 또는 none(알림 미수신 엣지케이스) 모두 연장
        # will_terminate(퇴실 확정) 상태는 제외하여 만료일에 정상 종료되도록 함
        template = sms_service.get_template('AUTO_EXTEND_PRE_NOTICE')
        offset = template.schedule_offset if template else -23
        target_extend_date = today - timedelta(days=offset)

        from app.models.contract import ContractStatusHistory
        from dateutil.relativedelta import relativedelta
        import calendar

        auto_extend_contracts = Contract.query.filter(
            Contract.status == 'active',
            Contract.end_date <= target_extend_date,  # == → <= : 배치 누락시에도 처리
            Contract.is_indefinite == False,
            db.or_(Contract.auto_extend_status.in_(['notified', 'none']), Contract.auto_extend_status.is_(None))
        ).all()

        for contract in auto_extend_contracts:
            # months가 0 또는 None이면 기본값 1 (안전장치)
            extend_months = contract.months if contract.months and contract.months > 0 else 1
            original_end = contract.end_date
            new_end_date = original_end + relativedelta(months=extend_months)

            # 말일 보정 로직: 기존 계약 종료일이 해당 월의 마지막 날짜였다면, 연장되는 월의 마지막 날짜로 맞춤
            original_last_day = calendar.monthrange(original_end.year, original_end.month)[1]
            if original_end.day == original_last_day:
                new_last_day = calendar.monthrange(new_end_date.year, new_end_date.month)[1]
                new_end_date = new_end_date.replace(day=new_last_day)

            # 이력 기록
            history = ContractStatusHistory(
                contract_id=contract.id,
                old_status=contract.status,
                new_status=contract.status,
                actor_type='system',
                source='batch',
                reason=f'계약 기간 자동 연장 (+{extend_months}개월) | 새 종료일: {new_end_date}'
            )
            db.session.add(history)

            # end_date 갱신 후 SMS 컨텍스트 생성 (갱신된 날짜 반영)
            contract.end_date = new_end_date
            contract.auto_extend_status = 'none'  # 초기화

            # related_date를 original_end로 설정해 같은 계약 중복 발송 방지
            context = build_sms_context(contract, 'AUTO_EXTEND_COMPLETED')
            sms_service.send_sms(contract.id, 'AUTO_EXTEND_COMPLETED', context, related_date=original_end)

        db.session.commit()

        print(f"[{now_kst}] Processed daily SMS tasks: Reminder({len(reminder_contracts)}), AutoRenewNotice({len(expiry_contracts)}), MoveoutDay({len(moveout_contracts)}), Welcome({len(welcome_contracts)}), AutoExtend15Days({len(auto_extend_contracts)})")
