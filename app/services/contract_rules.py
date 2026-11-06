"""Shared validation for booking periods and month-specific rent."""
import calendar
from datetime import date, datetime, timedelta, timezone
from werkzeug.exceptions import BadRequest, Conflict
from app.models.contract import Contract
from app.models.branch import Room

BLOCKING_STATUSES = ('requested', 'approved', 'waiting_signature', 'active', 'terminate_requested', 'extend_requested')

def positive_int(value, label, maximum=120):
    try:
        parsed = int(value)
    except (ValueError, TypeError, OverflowError):
        raise BadRequest(f'{label}은 양의 정수로 입력해주세요.')
    if isinstance(value, bool) or str(parsed) != str(value) or not 1 <= parsed <= maximum:
        raise BadRequest(f'{label}은 1~{maximum} 범위의 정수로 입력해주세요.')
    return parsed

def parse_date(value, label='날짜'):
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        raise BadRequest(f'{label}를 YYYY-MM-DD 형식으로 입력해주세요.')

def time_hours(start, end):
    def minutes(value):
        if value == '24:00':
            return 1440
        try:
            parsed = datetime.strptime(value, '%H:%M')
            if parsed.strftime('%H:%M') != value:
                raise ValueError()
            return parsed.hour * 60 + parsed.minute
        except (ValueError, TypeError):
            raise BadRequest('이용 시간을 HH:MM 형식으로 입력해주세요.')
    first, last = minutes(start), minutes(end)
    if first >= last or first >= 1440:
        raise BadRequest('종료 시간은 시작 시간보다 늦어야 합니다.')
    return (last - first) / 60

def ensure_available(room, start, end, start_time=None, end_time=None, exclude_id=None):
    if end < start:
        raise BadRequest('종료일은 시작일보다 빠를 수 없습니다.')
    if room.status == 'maintenance' or room.room_type == 'manager':
        raise Conflict('현재 신청할 수 없는 방입니다.')
    if room.room_type == 'time_based':
        time_hours(start_time, end_time)
    # Serialize changes for this room on databases supporting row locks.
    Room.query.filter_by(id=room.id).with_for_update().first()
    for other in Contract.query.filter(Contract.room_id == room.id, Contract.status.in_(BLOCKING_STATUSES)).with_for_update().all():
        if other.id == exclude_id:
            continue
        if room.room_type == 'time_based':
            overlaps = (other.start_date == start and other.start_time and other.end_time
                        and other.start_time < end_time and other.end_time > start_time)
        else:
            overlaps = other.start_date <= end and other.end_date >= start
        if overlaps:
            raise Conflict('해당 기간에 이미 예약 또는 계약이 존재합니다.')

def month_range(value=None):
    value = value or datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m')
    try:
        first = datetime.strptime(value, '%Y-%m').date()
        if first.strftime('%Y-%m') != value:
            raise ValueError()
    except (ValueError, TypeError):
        raise BadRequest('조회월을 YYYY-MM 형식으로 입력해주세요.')
    return first, first.replace(day=calendar.monthrange(first.year, first.month)[1])

def rent_amount(contract, month):
    from app.models.custom_discount import CustomDiscount
    discount = CustomDiscount.query.filter_by(contract_id=contract.id, target_month=month).first()
    base = contract.price if contract.price is not None else (contract.room.price or 0)
    amount = discount.amount if discount else 0
    return {'base_amount': base, 'discount_amount': amount, 'amount_due': max(0, base - amount),
            'discount_reason': discount.reason if discount else None}
