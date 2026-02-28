from flask import Blueprint, request, jsonify
from app.models.contract import Contract, TermsDocument
from app.models.branch import Room
from app.models.coupon import Coupon
from app.extensions import db
from app.routes.auth import token_required
from app.utils.evidence import log_contract_status_change, get_server_side_terms, generate_content_hash
import datetime
import json
from sqlalchemy import func

contract_bp = Blueprint('contract', __name__, url_prefix='/api/contracts')

def calculate_coupon_discount(room, months, coupon_code):
    """
    Calculate price breakdown with coupon.
    Returns dict with base_price, discounts, final prices.
    """
    coupon = None
    if coupon_code:
        coupon = Coupon.query.filter_by(code=coupon_code).first()

    # 1. Base Price (Room Price)
    base_price = room.price

    # 2. Monthly Promo Discount (Duration based)
    monthly_promo_discount = 0
    if months >= 12:
        monthly_promo_discount = 50000
    elif months >= 6:
        monthly_promo_discount = 30000
    elif months >= 3:
        monthly_promo_discount = 20000

    # 3. Initialize values
    coupon_discount = 0
    stack_policy = None
    discount_cycle = None
    coupon_id = None
    
    # 4. Coupon Logic
    if coupon:
        is_valid, msg = coupon.is_valid()
        if not is_valid:
            # If invalid, ignore coupon or raise error? 
            # For calculation, we treat as no coupon but return error msg if needed?
            # Calling function should handle validity check before calling this if they want to block.
            # Here we assume if passed, we try to apply.
            pass
        else:
            # Check conditions
            if coupon.min_months and months < coupon.min_months:
                pass # Condition not met
            else:
                coupon_id = coupon.id
                stack_policy = coupon.stack_policy
                discount_cycle = coupon.discount_cycle
                
                # Calculate Coupon Discount Value
                if coupon.discount_type == 'fixed':
                    coupon_discount = coupon.discount_value
                elif coupon.discount_type == 'percentage':
                    # Percentage of what? Base or Discounted?
                    # Usually Base Price for simplicity unless specified.
                    # Let's use Base Price to calculate the value amount.
                    coupon_discount = int(base_price * (coupon.discount_value / 100))

    # 5. Apply Stacking Policy
    # If EXCLUSIVE, remove monthly_promo_discount
    if stack_policy == 'EXCLUSIVE':
        monthly_promo_discount = 0
    
    # 6. Calculate Prices
    # Recurring Monthly Price
    if discount_cycle == 'monthly':
        final_monthly_price = base_price - monthly_promo_discount - coupon_discount
    else:
        # 'once' or No coupon
        final_monthly_price = base_price - monthly_promo_discount

    # First Month Price (Pre-proration)
    if discount_cycle == 'once':
        # Apply coupon to first month only
        # Base (with promo if stack) - Coupon
        first_month_price = (base_price - monthly_promo_discount) - coupon_discount
    else:
        # 'monthly' or No coupon
        first_month_price = final_monthly_price
        
    return {
        'base_price': base_price,
        'monthly_promo_discount': monthly_promo_discount,
        'coupon_discount': coupon_discount,
        'coupon_id': coupon_id,
        'stack_policy': stack_policy,
        'cycle': discount_cycle,
        'final_monthly_price': final_monthly_price,
        'first_month_price': first_month_price
    }, coupon

@contract_bp.route('/validate-coupon', methods=['POST'])
@token_required
def validate_coupon(current_user):
    data = request.get_json()
    room_id = data.get('room_id')
    months = data.get('months', 1)
    coupon_code = data.get('coupon_code')
    
    room = Room.query.get_or_404(room_id)
    
    if not coupon_code:
        return jsonify({'error': 'Coupon code required'}), 400
        
    coupon = Coupon.query.filter_by(code=coupon_code).first()
    if not coupon:
        return jsonify({'error': 'Invalid coupon code'}), 400
        
    is_valid, msg = coupon.is_valid()
    if not is_valid:
        return jsonify({'error': msg}), 400
        
    if coupon.min_months and months < coupon.min_months:
        return jsonify({'error': f'최소 {coupon.min_months}개월 이상 계약 시 사용 가능한 쿠폰입니다.'}), 400

    breakdown, _ = calculate_coupon_discount(room, months, coupon_code)
    
    return jsonify(breakdown)

@contract_bp.route('', methods=['POST'])
@token_required
def create_contract(current_user):
    data = request.get_json()
    room_id = data.get('room_id')
    start_date_str = data.get('start_date')
    months = data.get('months', 1)
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    coupon_code = data.get('coupon_code')
    
    room = Room.query.get_or_404(room_id)
    
    try:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'message': 'Invalid date format'}), 400

    payment_day = data.get('payment_day', 1)
        
    # Calculate end date
    if room.room_type == 'time_based':
        end_date = start_date
    # Calculate end date
    is_indefinite = data.get('is_indefinite', False)
    
    if room.room_type == 'time_based':
        end_date = start_date
    elif is_indefinite:
        # "한달 전 통보" (Indefinite) -> Set to far future (e.g., 2099-12-31)
        end_date = datetime.date(2099, 12, 31)
    else:
        # Simple month add (logic existed previously but imported calendar inside? Simplification here)
        try:
            # 시작일의 연/월과 지정한 payment_day로 기준일 설정
            anchor_date = start_date.replace(day=payment_day)
        except ValueError:
            # 예: 2월 31일 같은 경우 대비하여 해당 월의 마지막 날로 설정
            import calendar
            last_day = calendar.monthrange(start_date.year, start_date.month)[1]
            anchor_date = start_date.replace(day=last_day)
            
        import dateutil.relativedelta
        # 기준일로부터 n개월 뒤의 전날 종료 (프론트엔드와 일치)
        end_date = anchor_date + dateutil.relativedelta.relativedelta(months=months) - datetime.timedelta(days=1)
    
    # --- Price Calculation with Coupon ---
    breakdown, coupon = calculate_coupon_discount(room, months, coupon_code)
    
    # Verify Coupon Usage (Concurrency)
    if coupon:
        # Atomic Update
        if coupon.usage_limit:
            updated = db.session.query(Coupon).filter(
                Coupon.id == coupon.id, 
                Coupon.used_count < Coupon.usage_limit
            ).update({'used_count': Coupon.used_count + 1})
            
            if not updated:
                return jsonify({'error': 'Coupon usage limit exceeded'}), 400
        else:
             # Just increment if no limit, but still good to be atomic or just simple add
             coupon.used_count += 1
             # Note: simple add is not race-free but for no-limit it's less critical.
             # Better: Coupon.query.filter_by(id=coupon.id).update({'used_count': Coupon.used_count + 1})
             db.session.query(Coupon).filter(Coupon.id == coupon.id).update({'used_count': Coupon.used_count + 1})

    # Prorated Calculation (payment_day already extracted)
    
    # Parse start_date (already done)
    start_dt = start_date

    # Determine Anchor Date
    try:
        anchor_date = start_dt.replace(day=payment_day)
    except ValueError:
        # Handle invalid dates (e.g. Feb 30) -> move to next month 1st or last day?
        # Simple fallback: use 28th? or 1st of next month?
        # Implementation Detail: for now assume valid or fallback to 1.
        anchor_date = start_dt.replace(day=1) 

    diff_days = (anchor_date - start_dt).days
    
    # Proration Base
    # Logic: 
    # If cycle='monthly': Prorate on final_monthly_price
    # If cycle='once': Prorate on recurring price (final_monthly_price), and subtract coupon from result?
    # As discussed: 
    # 'monthly' cycle: Changes the monthly_price. Proration follows.
    # 'once' cycle: monthly_price is standard. Proration on standard. Then subtract coupon.
    
    # Recurring Monthly Price
    recurring_price = breakdown['final_monthly_price']
    
    # Get actual days in start month for better accuracy
    import calendar
    days_in_month = calendar.monthrange(start_dt.year, start_dt.month)[1]
    daily_rate = recurring_price / days_in_month
    proration_adjustment = int(diff_days * daily_rate)
    
    # Round to nearest 1000 won (as requested by user)
    # This applies to the adjustment amount itself, e.g. -193,333 -> -193,000 or -194,000
    # Standard Python round(val, -3) rounds to nearest 1000.
    proration_adjustment = int(round(proration_adjustment, -3))
    
    # Initial Payment Amount
    if breakdown['cycle'] == 'once':
        # Proration on recurring, then subtract coupon
        # But wait, `first_month_price` calculated in helper was `(Base - Promo) - Coupon`.
        # Taking `recurring_price` (which is Base - Promo) + Proration - Coupon
        final_price = recurring_price + proration_adjustment - breakdown['coupon_discount']
    else:
        # cycle = monthly or None
        # recurring_price has the discount baked in.
        final_price = recurring_price + proration_adjustment
    
    # Apply VAT only if card
    payment_method = data.get('payment_method', 'bank')
    if payment_method == 'card':
        final_price = int(final_price * 1.1)

    # breakdown 업데이트 (프론트엔드 표시용)
    breakdown['proration_adjustment'] = proration_adjustment
    breakdown['first_month_rent'] = final_price # 일할 계산 + VAT 적용된 첫 달 임대료 부분
    breakdown['first_month_total'] = final_price + (room.deposit if room.room_type != 'time_based' else 0)

    # --- Evidence Capture (New) ---
    terms_version = data.get('terms_version')
    terms_doc = None
    if terms_version:
        terms_doc = get_server_side_terms(terms_version)
    
    # Capture env info
    consent_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    consent_user_agent = request.headers.get('User-Agent')

    contract = Contract(
        user_id=current_user.id,
        room_id=room.id,
        start_date=start_date,
        end_date=end_date,
        start_time=start_time,
        end_time=end_time,
        payment_method=payment_method,
        payment_day=payment_day,
        months=months if room.room_type != 'time_based' else 0,
        price=breakdown['final_monthly_price'] * (data.get('hours', 1) if room.room_type == 'time_based' else 1), # Storing Recurring Price
        deposit=room.deposit if room.room_type != 'time_based' else 0,
        status='requested',
        coupon_id=breakdown['coupon_id'],
        discount_details=json.dumps(breakdown),
        is_indefinite=is_indefinite,
        
        # Evidence Fields
        terms_document_id=terms_doc.id if terms_doc else None,
        terms_version=terms_version,
        terms_snapshot_hash=terms_doc.content_hash if terms_doc else None,
        consented_at=datetime.datetime.utcnow(),
        consent_ip=consent_ip,
        consent_user_agent=consent_user_agent,
        consent_method=data.get('consent_method', 'checkbox_v1'),
        
        pricing_snapshot=breakdown, # Dict saved as JSON
        contract_email_snapshot=current_user.email
    )
    
    db.session.add(contract)
    db.session.flush() # Get ID for history
    
    # Audit History
    log_contract_status_change(
        contract=contract,
        old_status=None,
        new_status='requested',
        actor_id=current_user.id,
        actor_type='user',
        source='public_api'
    )
    
    db.session.commit()
    
    # --- SMS Trigger (New) ---
    try:
        from app.utils.sms_service import sms_service
        from app.utils.sms_context import build_sms_context
        context = build_sms_context(contract, 'CONTRACT_APPLIED', amount=format(final_price, ','))
        sms_service.send_sms(contract.id, 'CONTRACT_APPLIED', context)
    except Exception as e:
        # Don't block contract creation if SMS fails, but log it
        print(f"SMS trigger error: {e}")

    return jsonify({
        'id': contract.id,
        'status': contract.status,
        'price': contract.price, # Recurring Price
        'initial_payment': final_price, # Actual amount to pay now
        'deposit': contract.deposit
    }), 201

@contract_bp.route('', methods=['GET'])
@token_required
def get_my_contracts(current_user):
    contracts = current_user.contracts.all()
    result = []
    for c in contracts:
        custom_discounts_data = []
        for cd in c.custom_discounts:
            custom_discounts_data.append({
                'id': cd.id,
                'target_month': cd.target_month,
                'amount': cd.amount,
                'reason': cd.reason
            })

        result.append({
            'id': c.id,
            'room': {
                'id': c.room.id,
                'name': c.room.name,
                'room_type': c.room.room_type,
                'price': c.room.price,
                'deposit': c.room.deposit,
                'branch': {
                    'name': c.room.branch.name if c.room.branch else '알 수 없음'
                }
            },
            'start_date': c.start_date.isoformat(),
            'end_date': c.end_date.isoformat(),
            'is_indefinite': c.is_indefinite,
            'price': c.price,
            'deposit': c.deposit,
            'status': c.status,
            'payment_day': c.payment_day,
            'payment_method': c.payment_method,
            'discount_details': json.loads(c.discount_details) if c.discount_details else None,
            'coupon_name': c.coupon.name if c.coupon else None,
            'termination_effective_date': c.termination_effective_date.strftime('%Y-%m-%d') if c.termination_effective_date else None,
            'custom_discounts': custom_discounts_data
        })
    return jsonify(result)
