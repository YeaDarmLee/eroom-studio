from datetime import datetime, timedelta
from app.models.sms import get_kst_now

def build_sms_context(contract, msg_type):
    """
    계약 객체와 SMS 타입에 기반하여 템플릿 치환을 위한 컨텍스트 변수 사전을 생성합니다.
    """
    user_info = contract.get_user_info()
    today = get_kst_now().date()
    
    # 기본 컨텍스트
    context = {
        'user_name': user_info['name'],
        'user_phone': user_info['phone'],
        'branch_name': contract.room.branch.name if contract.room and contract.room.branch else '이룸 스튜디오',
        'room_name': contract.room.name if contract.room else 'N/A',
        'start_date': contract.start_date.strftime('%Y-%m-%d') if contract.start_date else '',
        'end_date': contract.end_date.strftime('%Y-%m-%d') if contract.end_date else '',
    }

    # 타입별 추가 컨텍스트
    if msg_type in ['PAYMENT_REMINDER', 'PAYMENT_OVERDUE_STAGE1', 'PAYMENT_OVERDUE_STAGE2']:
        # 납부 예정일/연체일 계산
        # 수동 발송 시점의 '가장 가까운 납부일'을 추정
        # 오늘이 20일, 납부일이 25일 -> 이번달 25일
        # 오늘이 26일, 납부일이 25일 -> 이번달 25일 (이미 지남 - 연체) or 다음달 25일?
        # REMINDER의 경우 미래, OVERDUE의 경우 과거를 가르켜야 함.
        pass # 아래에서 구체화
        
        # Default Logic: Current Month's Payment Day
        # If Current Day > Payment Day + 5 (Stage 2), maybe Next Month?
        # But 'MANUAL' implies admin wants to send about *current situation*.
        
        target_year = today.year
        target_month = today.month
        
        # Handle month overflow/underflow if needed, but simple replacement is safer for now.
        # But careful with days like 31st.
        try:
            current_month_due = today.replace(day=contract.payment_day)
        except ValueError:
            # e.g. Feb 30 -> Feb 28/29
            # Skip complex logic for now, just use today or 1st of next month - 1 day?
            # Let's simple check:
            if today.month == 12:
                next_month = today.replace(year=today.year+1, month=1, day=1)
            else:
                next_month = today.replace(month=today.month+1, day=1)
            current_month_end = next_month - timedelta(days=1)
            current_month_due = current_month_end # Fallback to last day
        
        context['due_date'] = current_month_due.strftime('%Y-%m-%d')
        context['amount'] = format(int(contract.price or 0), ',')

    elif msg_type == 'AUTO_RENEW_NOTICE':
        # Renew deadline default: End Date - 30 days (or use schedule_offset if available via DB lookup, but context builder shouldn't do DB lookup easily)
        # We'll use the calculation `end_date - 30` as a safe default for manual send.
        if contract.end_date:
            context['renew_deadline'] = (contract.end_date - timedelta(days=30)).strftime('%Y-%m-%d')

    elif msg_type == 'MOVEOUT_APPROVED':
        # Deposit Refund: End Date + 3 days
        if contract.end_date:
            context['deposit_refund_date'] = (contract.end_date + timedelta(days=3)).strftime('%Y-%m-%d')
            context['moveout_date'] = contract.end_date.strftime('%Y-%m-%d')
            
    elif msg_type == 'MOVEOUT_APPLIED':
        if contract.end_date:
            context['moveout_date'] = contract.end_date.strftime('%Y-%m-%d')

    return context
