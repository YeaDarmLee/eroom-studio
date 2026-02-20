from datetime import datetime, timedelta
from app.models.sms import get_kst_now

def build_sms_context(contract, msg_type, **kwargs):
    """
    계약 객체와 SMS 타입에 기반하여 템플릿 치환을 위한 컨텍스트 변수 사전을 생성합니다.
    kwargs를 통해 수동으로 변수들을 주입하거나 덮어쓸 수 있습니다.
    """
    user_info = contract.get_user_info()
    today = get_kst_now().date()
    
    # 기본 컨텍스트 (모든 타입 공통)
    context = {
        'user_name': user_info['name'],
        'user_phone': user_info['phone'],
        'branch_name': contract.room.branch.name if contract.room and contract.room.branch else '이룸 스튜디오',
        'room_name': contract.room.name if contract.room else 'N/A',
        'start_date': contract.start_date.strftime('%Y-%m-%d') if contract.start_date else '',
        'end_date': contract.end_date.strftime('%Y-%m-%d') if contract.end_date else '',
    }

    # 타입별 특화 로직
    if msg_type == 'CONTRACT_APPROVED':
        context['due_date'] = f"매월 {contract.payment_day}일"

    elif msg_type in ['PAYMENT_REMINDER', 'PAYMENT_OVERDUE_STAGE1', 'PAYMENT_OVERDUE_STAGE2']:
        context['amount'] = format(int(contract.price or 0), ',')
        # date_override가 있으면 사용 (tasks.py 등에서 계산된 날짜)
        due_date = kwargs.get('due_date')
        if not due_date:
            # 기본값: 이번 달 납부일 계산
            try:
                due_date_obj = today.replace(day=contract.payment_day)
            except ValueError:
                # 말일 처리 (2월 30일 등)
                import calendar
                last_day = calendar.monthrange(today.year, today.month)[1]
                due_date_obj = today.replace(day=last_day)
            due_date = due_date_obj.strftime('%Y-%m-%d')
        context['due_date'] = due_date

    elif msg_type == 'AUTO_RENEW_NOTICE':
        context['end_date'] = contract.end_date.strftime('%Y-%m-%d') if contract.end_date else ''
        # renew_deadline: 보통 종료 30일 전
        renew_deadline = kwargs.get('renew_deadline')
        if not renew_deadline and contract.end_date:
            renew_deadline = (contract.end_date - timedelta(days=30)).strftime('%Y-%m-%d')
        context['renew_deadline'] = renew_deadline or today.strftime('%Y-%m-%d')

    elif msg_type == 'MOVEOUT_APPROVED':
        moveout_date = kwargs.get('moveout_date') or (contract.end_date.strftime('%Y-%m-%d') if contract.end_date else today.strftime('%Y-%m-%d'))
        context['moveout_date'] = moveout_date
        # 보증금 반환일: 퇴실 3일 후 (기본값)
        if contract.end_date:
            context['deposit_refund_date'] = (contract.end_date + timedelta(days=3)).strftime('%Y-%m-%d')

    elif msg_type == 'MOVEOUT_APPLIED':
        context['moveout_date'] = kwargs.get('moveout_date') or (contract.end_date.strftime('%Y-%m-%d') if contract.end_date else '')

    elif msg_type == 'CONTRACT_APPLIED':
        # 계약 신청 시 실시간 결제 금액 (첫 달 금액 등)이 있으면 amount로 사용
        if 'amount' in kwargs:
            context['amount'] = kwargs['amount']

    # 추가 주입된 모든 변수 반영 (덮어쓰기 허용)
    context.update(kwargs)
    
    return context

def get_dummy_context():
    """SMS 템플릿 미리보기 및 바이트 계산을 위한 더미 컨텍스트를 반환합니다."""
    return {
        'user_name': '홍길동',
        'branch_name': '강남점',
        'room_name': '101호',
        'start_date': '2024-03-01',
        'end_date': '2024-04-01',
        'due_date': '매월 1일',
        'amount': '500,000',
        'moveout_date': '2024-04-30',
        'renew_deadline': '2024-03-02',
        'deposit_refund_date': '2024-05-07',
        'user_phone': '010-1234-5678'
    }
