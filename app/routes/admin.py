from flask import Blueprint, request, jsonify, current_app, render_template
from app.extensions import db
from app.models.contract import Contract, TermsDocument
from app.models.user import User
from app.models.branch import Branch, Room, BranchFloor, RoomImage, BranchImage
from app.models.sms import SmsTemplate, SmsLog
from app.utils.evidence import log_contract_status_change, ensure_private_dir
from app.utils.sms_service import sms_service, SMS_VARIABLE_SCHEMA
from app.utils.sms_service import sms_service, SMS_VARIABLE_SCHEMA
from app.utils.sms_context import build_sms_context, get_dummy_context
from app.models.coupon import Coupon
from app.models.request import Request
from app.routes.auth import admin_required
from app.utils.db_utils import db_retry
from app.services.contract_mapping_service import ContractMappingService
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import json
import os
import uuid
import math
from app.utils.sms_context import build_sms_context
from functools import wraps
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy import func, case

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@admin_required
def dashboard(current_user):
    """Admin dashboard page"""
    return render_template('admin/dashboard.html')

@admin_bp.route('/api/stats', methods=['GET'])
@admin_required
@db_retry(max_retries=3, delay=1)
def get_stats(current_user):
    """Get dashboard stats (Optimized)"""
    
    # 1. Basic Counts
    total_users = User.query.count()
    active_contracts_count = Contract.query.filter_by(status='active').count()
    pending_contracts = Contract.query.filter_by(status='requested').count()
    pending_requests = Request.query.filter_by(status='submitted').count() + pending_contracts
    
    # 2. Revenue & Deposit (Active Contracts)
    # Use SQL aggregation for performance
    # Price: if c.price is not null use it, else if c.room.price use it, else 0
    # SQLite/MySQL compatible 'coalesce' logic
    
    revenue_query = db.session.query(
        func.sum(
            case(
                (Contract.price != None, Contract.price),
                else_=Room.price
            )
        ).label('total_revenue'),
        func.sum(
            case(
                (Contract.deposit != None, Contract.deposit),
                else_=Room.deposit
            )
        ).label('total_deposit')
    ).select_from(Contract).join(Room).filter(Contract.status == 'active')
    
    revenue_result = revenue_query.first()
    total_monthly_revenue = revenue_result.total_revenue or 0
    total_deposit = revenue_result.total_deposit or 0

    # 3. Expiring Contracts (Active, Not Indefinite, End Date <= 30 days)
    one_month_from_now = (datetime.utcnow() + timedelta(days=30)).date()
    expiring_count = Contract.query.filter(
        Contract.status == 'active',
        Contract.is_indefinite == False,
        Contract.end_date != None,
        Contract.end_date <= one_month_from_now
    ).count()

    # 4. Room Stats (Occupied/Available) by Branch
    # We need to list branches with their stats.
    
    # Get all branches with active contracts in one query
    # We want: Branch ID, Name, Revenue, Deposit, Contract Count, Expiring Count
    
    # Subquery for branch stats from contracts
    contract_stats = db.session.query(
        Room.branch_id,
        func.sum(
            case((Contract.price != None, Contract.price), else_=Room.price)
        ).label('revenue'),
        func.sum(
            case((Contract.deposit != None, Contract.deposit), else_=Room.deposit)
        ).label('deposit'),
        func.sum(
            case((
                (Contract.is_indefinite == False) & 
                (Contract.end_date != None) & 
                (Contract.end_date <= one_month_from_now), 1
            ), else_=0)
        ).label('expiring')
    ).select_from(Contract).join(Room).filter(Contract.status == 'active').group_by(Room.branch_id).all()
    
    branch_stats_map = {r.branch_id: r for r in contract_stats}
    
    # Get all rooms to calculate occupancy per branch
    # Group by branch_id and room_type (active/monthly/etc) isn't direct on Room
    # easier to fetch all rooms (lighter than contracts) or aggregate rooms
    
    # Count total rooms per branch
    total_rooms_per_branch = db.session.query(
        Room.branch_id, 
        func.count(Room.id).label('total')
    ).group_by(Room.branch_id).all()
    
    # Count occupied rooms per branch (based on active contracts)
    occupied_rooms_per_branch = db.session.query(
        Room.branch_id,
        func.count(Room.id).label('occupied')
    ).join(Contract, (Contract.room_id == Room.id) & (Contract.status == 'active')).group_by(Room.branch_id).all()

    # Count monthly rooms per branch
    monthly_rooms_per_branch = db.session.query(
        Room.branch_id,
        func.count(Room.id).label('monthly_total')
    ).filter(Room.room_type == 'monthly').group_by(Room.branch_id).all()
    
    # Count occupied monthly rooms per branch
    occupied_monthly_rooms_per_branch = db.session.query(
        Room.branch_id,
        func.count(Room.id).label('monthly_occupied')
    ).join(Contract, (Contract.room_id == Room.id) & (Contract.status == 'active')).filter(Room.room_type == 'monthly').group_by(Room.branch_id).all()
    
    # Detailed counts by type
    manager_rooms_per_branch = db.session.query(Room.branch_id, func.count(Room.id)).filter(Room.room_type == 'manager').group_by(Room.branch_id).all()
    time_rooms_per_branch = db.session.query(Room.branch_id, func.count(Room.id)).filter(Room.room_type == 'time_based').group_by(Room.branch_id).all()

    # Maps for easy lookup
    total_rooms_map = {r.branch_id: r.total for r in total_rooms_per_branch}
    occupied_rooms_map = {r.branch_id: r.occupied for r in occupied_rooms_per_branch}
    monthly_rooms_map = {r.branch_id: r.monthly_total for r in monthly_rooms_per_branch}
    occupied_monthly_rooms_map = {r.branch_id: r.monthly_occupied for r in occupied_monthly_rooms_per_branch}
    manager_rooms_map = {r.branch_id: r[1] for r in manager_rooms_per_branch}
    time_rooms_map = {r.branch_id: r[1] for r in time_rooms_per_branch}

    branches = Branch.query.all()
    branch_data = []
    
    total_monthly_rooms_all = 0
    occupied_monthly_rooms_all = 0
    occupied_rooms_all = 0
    total_rooms_all = 0

    for branch in branches:
        bid = branch.id
        stats = branch_stats_map.get(bid)
        
        b_revenue = stats.revenue if stats and stats.revenue else 0
        b_deposit = stats.deposit if stats and stats.deposit else 0
        b_expiring = stats.expiring if stats and stats.expiring else 0
        
        b_total_rooms = total_rooms_map.get(bid, 0)
        b_occupied_rooms = occupied_rooms_map.get(bid, 0)
        b_monthly_rooms = monthly_rooms_map.get(bid, 0)
        b_occupied_monthly = occupied_monthly_rooms_map.get(bid, 0)
        
        b_available_rooms = b_monthly_rooms - b_occupied_monthly
        
        # Collect unoccupied monthly rooms
        occupied_room_ids = {r.room_id for r in Contract.query.filter_by(status='active').with_entities(Contract.room_id).all()}
        # branch.rooms is lazy='dynamic', so we need to call .all()
        available_rooms_list = [
            {'id': r.id, 'name': r.name, 'price': r.price, 'deposit': r.deposit} 
            for r in branch.rooms.all() 
            if r.room_type == 'monthly' and r.id not in occupied_room_ids
        ]
        
        branch_data.append({
            'id': branch.id,
            'name': branch.name,
            'monthly_revenue': b_revenue,
            'deposit': b_deposit,
            'total_rooms': b_total_rooms,
            'occupied_rooms': b_occupied_rooms,
            'available_rooms': b_available_rooms,
            'available_rooms_list': available_rooms_list,
            'expiring_contracts': b_expiring,
            'monthly_rooms': b_monthly_rooms,
            'time_based_rooms': time_rooms_map.get(bid, 0),
            'manager_rooms': manager_rooms_map.get(bid, 0),
            'total_monthly_rooms': b_monthly_rooms
        })
        
        total_monthly_rooms_all += b_monthly_rooms
        occupied_monthly_rooms_all += b_occupied_monthly
        occupied_rooms_all += b_occupied_rooms
        total_rooms_all += b_total_rooms
    
    # Final global stats
    # Fetch room types counts globally
    global_monthly = Room.query.filter_by(room_type='monthly').count()
    global_time = Room.query.filter_by(room_type='time_based').count()
    global_manager = Room.query.filter_by(room_type='manager').count()
    
    return jsonify({
        'stats': {
            'totalUsers': total_users,
            'activeContracts': active_contracts_count,
            'pendingRequests': pending_requests,
            'expiringContracts': expiring_count,
            'monthlyRevenue': total_monthly_revenue,
            'totalDeposit': total_deposit,
            'totalRooms': total_rooms_all,
            'occupiedRooms': occupied_rooms_all,
            'availableRooms': global_monthly - occupied_monthly_rooms_all, # 공실은 월세방 기준
            'monthlyRooms': global_monthly,
            'timeBasedRooms': global_time,
            'managerRooms': global_manager,
            'totalMonthlyRooms': global_monthly
        },
        'branchData': branch_data
    })

@admin_bp.route('/api/contracts', methods=['GET'])
@admin_required
@db_retry(max_retries=3, delay=1)
def get_contracts(current_user):
    """Get all contracts with details (including unmapped contracts)"""
    contracts = Contract.query.options(
        joinedload(Contract.user),
        joinedload(Contract.room).joinedload(Room.branch),
        joinedload(Contract.coupon)
    ).all()
    result = []
    
    for c in contracts:
        user_info = c.get_user_info()
        contract_data = {
            'id': c.id,
            'user_name': user_info['name'] or '알 수 없음',
            'user_email': user_info['email'] or '',
            'user_id': user_info['id'],
            'user_phone': user_info['phone'] or '',
            'is_mapped': user_info['is_mapped'],
            'room_id': c.room_id,
            'room_name': c.room.name if c.room else '알 수 없음',
            'room_type': c.room.room_type if c.room else 'monthly',
            'branch_id': c.room.branch_id if c.room else None,
            'branch_name': c.room.branch.name if c.room and c.room.branch else '알 수 없음',
            'deposit': c.deposit if c.deposit is not None else (c.room.deposit if c.room else 0),
            'price': c.price if c.price is not None else (c.room.price if c.room else 0),
            'start_date': c.start_date.strftime('%Y-%m-%d'),
            'end_date': c.end_date.strftime('%Y-%m-%d'),
            'start_time': c.start_time,
            'end_time': c.end_time,
            'payment_day': c.payment_day,
            'payment_method': c.payment_method,
            'status': c.status,
            'discount_details': json.loads(c.discount_details) if c.discount_details else None,
            'coupon_name': c.coupon.name if c.coupon else None,
            'is_indefinite': c.is_indefinite,
            'termination_effective_date': c.termination_effective_date.strftime('%Y-%m-%d') if c.termination_effective_date else None,
            'created_at': c.created_at.strftime('%Y-%m-%d %H:%M') if c.created_at else ''
        }
        result.append(contract_data)
    
    return jsonify(result)


@admin_bp.route('/api/contracts/<int:id>', methods=['GET'])
@admin_required
@db_retry(max_retries=3, delay=1)
def get_contract_detail(current_user, id):
    """Get single contract details"""
    c = Contract.query.get_or_404(id)
    user_info = c.get_user_info()
    
    contract_data = {
        'id': c.id,
        'user_name': user_info['name'] or '알 수 없음',
        'user_email': user_info['email'] or '',
        'user_id': user_info['id'],
        'user_phone': user_info['phone'] or '',
        'is_mapped': user_info['is_mapped'],
        'room_id': c.room_id,
        'room_name': c.room.name if c.room else '알 수 없음',
        'room_type': c.room.room_type if c.room else 'monthly',
        'branch_id': c.room.branch_id if c.room else None,
        'branch_name': c.room.branch.name if c.room and c.room.branch else '알 수 없음',
        'deposit': c.deposit if c.deposit is not None else (c.room.deposit if c.room else 0),
        'price': c.price if c.price is not None else (c.room.price if c.room else 0),
        'start_date': c.start_date.strftime('%Y-%m-%d'),
        'end_date': c.end_date.strftime('%Y-%m-%d'),
        'start_time': c.start_time,
        'end_time': c.end_time,
        'payment_day': c.payment_day,
        'payment_method': c.payment_method,
        'status': c.status,
        'discount_details': json.loads(c.discount_details) if c.discount_details else None,
        'coupon_name': c.coupon.name if c.coupon else None,
        'is_indefinite': c.is_indefinite,
        'termination_effective_date': c.termination_effective_date.strftime('%Y-%m-%d') if c.termination_effective_date else None,
        'created_at': c.created_at.strftime('%Y-%m-%d %H:%M') if c.created_at else ''
    }
    
    return jsonify(contract_data)

@admin_bp.route('/api/contracts', methods=['POST'])
@admin_required
def create_contract(current_user):
    """수동 계약 생성"""
    data = request.get_json()
    
    is_indefinite = data.get('is_indefinite', False)
    
    # Validation
    if not data.get('room_id') or not data.get('start_date') or (not is_indefinite and not data.get('end_date')):
        return jsonify({'error': '방, 시작일, 종료일(또는 무기한)은 필수입니다.'}), 400
        
    room = Room.query.get(data['room_id'])
    if not room:
        return jsonify({'error': '방을 찾을 수 없습니다.'}), 404
        
    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    
    if is_indefinite:
        end_date = date(2099, 12, 31)
        months = 0 # Or 1? Usually irrelevant for indefinite
    else:
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        # Calculate months roughly
        delta = end_date - start_date
        months = round(delta.days / 30)
        if months < 1: months = 1
    
    contract = Contract(
        user_id=data.get('user_id') or None, # Optional: Ensure empty string becomes None
        room_id=room.id,
        start_date=start_date,
        end_date=end_date,
        price=data.get('price', room.price),       # Use provided price or room default
        deposit=data.get('deposit', room.deposit), # Use provided deposit or room default
        months=months,
        payment_day=data.get('payment_day', 1), # Default to 1st
        status='active', # Default to active for manual creation
        is_indefinite=is_indefinite,
        created_at=datetime.now()
    )
    
    # If user_id is NOT provided, we might want to store temp info if provided
    if not data.get('user_id'):
        contract.temp_user_name = data.get('user_name')
        contract.temp_user_phone = data.get('user_phone')
        
    db.session.add(contract)
    
    # Update room status if contract is active
    if contract.status == 'active':
        room.status = 'occupied'
        
    db.session.commit()
    
    return jsonify({'message': 'Contract created', 'id': contract.id}), 201

@admin_bp.route('/api/contracts/<int:id>', methods=['PUT'])
@admin_required
def update_contract(current_user, id):
    """계약 정보 수정"""
    contract = Contract.query.get_or_404(id)
    data = request.get_json()
    
    if 'room_id' in data:
        room = Room.query.get(data['room_id'])
        if not room:
            return jsonify({'error': '방을 찾을 수 없습니다.'}), 404
        
        # 만약 방이 바뀌는 경우, 이전 방과 새 방의 상태를 업데이트해야 할 수 있음
        if contract.room_id != room.id:
            # 이전 방은 비어있게 (단, 다른 활성 계약이 없는 경우만 - 복잡하므로 일단 로그만)
            if contract.room:
                contract.room.status = 'available'
            contract.room_id = room.id
            if contract.status == 'active':
                room.status = 'occupied'
    
    if 'is_indefinite' in data:
        contract.is_indefinite = data['is_indefinite']
        
    if 'start_date' in data:
        contract.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        
    if contract.is_indefinite:
        contract.end_date = date(2099, 12, 31)
    elif 'end_date' in data and data['end_date']:
        contract.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
    if 'price' in data:
        contract.price = data['price']
    if 'deposit' in data:
        contract.deposit = data['deposit']
    if 'start_time' in data:
        contract.start_time = data['start_time']
    if 'end_time' in data:
        contract.end_time = data['end_time']
        
    if 'user_id' in data:
        contract.user_id = data['user_id'] or None
        
    # 미매핑 정보 업데이트
    if 'user_name' in data:
        contract.temp_user_name = data['user_name']
    if 'user_phone' in data:
        contract.temp_user_phone = data['user_phone']
    if 'user_email' in data:
        contract.temp_user_email = data['user_email']

    # Recalculate months if dates changed
    if 'start_date' in data or 'end_date' in data:
        delta = contract.end_date - contract.start_date
        months = round(delta.days / 30)
        if months < 1: months = 1
        contract.months = months

    if 'payment_day' in data:
        try:
            contract.payment_day = int(data['payment_day'])
        except (ValueError, TypeError):
            pass

    db.session.commit()
    return jsonify({'message': 'Contract updated'})

@admin_bp.route('/api/monthly-payments', methods=['GET'])
@admin_required
def get_monthly_payments(current_user):
    """Get active contracts grouped by payment day"""
    active_contracts = Contract.query.filter_by(status='active').all()
    
    day1 = []
    day15 = []
    others = []
    
    for c in active_contracts:
        user_info = c.get_user_info()
        item = {
            'id': c.id,
            'user_name': user_info['name'] or c.temp_user_name or '알 수 없음',
            'room_name': c.room.name if c.room else '알 수 없음',
            'branch_name': c.room.branch.name if c.room and c.room.branch else '알 수 없음',
            'price': c.price if c.price is not None else (c.room.price if c.room else 0),
            'payment_day': c.payment_day,
            'user_phone': user_info.get('phone') or ''
        }
        
        if c.payment_day == 1:
            day1.append(item)
        elif c.payment_day == 15:
            day15.append(item)
        else:
            others.append(item)
            
    # Sort others by payment day
    others.sort(key=lambda x: (x['payment_day'] or 0))
    
    return jsonify({
        'day1': day1,
        'day15': day15,
        'others': others
    })

@admin_bp.route('/api/requests', methods=['GET'])
@admin_required
@db_retry(max_retries=3, delay=1)
def get_requests(current_user):
    """Get all requests and inquiries"""
    requests = Request.query.order_by(Request.created_at.desc()).all()
    results = []
    for r in requests:
        details_data = {}
        if r.details:
            try:
                details_data = json.loads(r.details)
            except:
                details_data = {'raw': r.details}
        
        branch_id = None
        if r.contract and r.contract.room:
            branch_id = r.contract.room.branch_id
        elif details_data.get('branch_id'):
            branch_id = details_data.get('branch_id')

        results.append({
            'id': r.id,
            'user_name': r.user.name if r.user else '알 수 없음',
            'type': r.type,
            'status': r.status,
            'details': details_data,
            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M'),
            'room_name': r.contract.room.name if r.contract and r.contract.room else (details_data.get('room_name') or 'N/A'),
            'branch_id': branch_id
        })
    return jsonify(results)

@admin_bp.route('/api/contracts/<int:id>/status', methods=['PUT'])
@admin_required
def update_contract_status(current_user, id):
    """Update contract status and sync room status"""
    contract = Contract.query.get_or_404(id)
    data = request.get_json()
    
    if 'status' in data:
        old_status = contract.status
        new_status = data['status']
        
        # --- Future Termination Logic (New) ---
        today = datetime.utcnow().date()
        effective_status = new_status
        
        # If admin is "terminating" or "approving termination", check the date
        if new_status == 'terminated':
            target_date = contract.termination_effective_date or (contract.end_date if not contract.is_indefinite else None)
            if target_date and target_date > today:
                import json
                
                # Future termination: Set to active but with fixed end_date
                effective_status = 'active'
                contract.is_indefinite = False
                
                # Sync end_date if needed
                if contract.termination_effective_date:
                    contract.end_date = contract.termination_effective_date
                
                # Mark original termination request as done (if any)
                termination_req = next((r for r in contract.requests if r.type == 'termination' and r.status != 'done'), None)
                if termination_req:
                    termination_req.status = 'done'
                    try:
                        details_dict = json.loads(termination_req.details) if termination_req.details else {}
                    except:
                        details_dict = {'raw': termination_req.details}
                    details_dict['processed_at'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                    details_dict['admin_response'] = '해지 승인 완료'
                    termination_req.details = json.dumps(details_dict)
        
        # 1. Update Status with History
        contract.status = effective_status
        log_contract_status_change(
            contract=contract,
            old_status=old_status,
            new_status=effective_status,
            actor_id=current_user.id,
            actor_type='admin',
            source='admin_ui',
            reason=data.get('reason')
        )
        
        # 2. Automated Evidence/Notice on Approval
        # Only trigger when status changes to approved/active
        if effective_status in ['approved', 'active'] and old_status != effective_status:
            # Store initial notice info
            contract.notice_email_to = contract.contract_email_snapshot or contract.get_user_info()['email']
            
            # TODO: PDF Generation (Stub)
            # pdf_data = generate_summary_pdf(contract)
            # save_contract_pdf(contract.id, pdf_data)
            # contract.contract_pdf_hash = ...
            
            # TODO: Email Dispatch (Stub)
            # contract.notice_email_attempts += 1
            # contract.contract_notice_sent_at = datetime.now()
            
            # --- SMS Trigger (New) ---
            try:
                from app.utils.sms_service import sms_service
                user_info = contract.get_user_info()
                
                # Debug Logging to File
                with open('sms_debug.txt', 'a', encoding='utf-8') as f:
                    f.write(f"\n[{datetime.now()}] Triggering for Contract {contract.id}\n")
                    f.write(f"Old Status: {old_status}, New Status: {effective_status}\n")
                    f.write(f"User Phone: {user_info.get('phone')}\n")
                    f.write(f"Start Date: {contract.start_date}\n")
                    f.write(f"Payment Day: {contract.payment_day}\n")

                context = build_sms_context(contract, 'CONTRACT_APPROVED')
                
                success, msg = sms_service.send_sms(contract.id, 'CONTRACT_APPROVED', context)
                
                with open('sms_debug.txt', 'a', encoding='utf-8') as f:
                    f.write(f"send_sms result: success={success}, msg={msg}\n")
            except Exception as e:
                with open('sms_debug.txt', 'a', encoding='utf-8') as f:
                    f.write(f"SMS trigger error (APPROVED): {str(e)}\n")
                print(f"SMS trigger error (APPROVED): {e}")

        # --- SMS Trigger (New: Termination Approval) ---
        if new_status == 'terminated' or (effective_status == 'terminate_requested' and old_status != effective_status):
             # Also send if it's a termination request being processed
             # We check if there's a pending termination request to avoid double-sending
             # (though force_send=True is used, it's safer to check context)
             termination_req = next((r for r in contract.requests if r.type == 'termination' and r.status != 'done'), None)
             if termination_req or (new_status == 'terminated' and old_status != 'terminated'):
                try:
                    from app.utils.sms_service import sms_service
                    from app.utils.sms_context import build_sms_context
                    context = build_sms_context(contract, 'MOVEOUT_APPROVED')
                    sms_service.send_sms(contract.id, 'MOVEOUT_APPROVED', context)
                except Exception as e:
                    print(f"SMS trigger error (MOVEOUT_APPROVED): {e}")

        # 3. Sync room status with contract status
        if contract.room:
            if effective_status == 'active':
                contract.room.status = 'occupied'
            elif effective_status in ['terminated', 'cancelled']:
                # Set back to available when contract ends or is cancelled
                contract.room.status = 'available'
            elif effective_status == 'terminate_requested':
                # Ensure it stays occupied if it's a future termination
                contract.room.status = 'occupied'
            elif effective_status == 'approved':
                contract.room.status = 'reserved'

        # 4. Sync Request Status (Termination)
        if effective_status in ['terminated', 'terminate_requested']:
            # Mark any pending termination request as 'done'
            termination_reqs = Request.query.filter_by(
                contract_id=id, 
                type='termination'
            ).filter(Request.status != 'done').all()
            for r in termination_reqs:
                r.status = 'done'
            
            # --- SMS Trigger (New) ---
            try:
                from app.utils.sms_service import sms_service
                from app.utils.sms_context import build_sms_context
                context = build_sms_context(contract, 'MOVEOUT_APPROVED')
                sms_service.send_sms(contract.id, 'MOVEOUT_APPROVED', context)
            except Exception as e:
                print(f"SMS trigger error (MOVEOUT_APPROVED): {e}")
        
        elif new_status == 'active' and old_status == 'terminate_requested':
            # Mark any pending termination request as 'cancelled' (Rejected case)
            termination_reqs = Request.query.filter_by(
                contract_id=id, 
                type='termination'
            ).filter(Request.status != 'done').all()
            for r in termination_reqs:
                r.status = 'cancelled'
            
            # --- SMS Trigger (New) ---
            # NOTE: If we have a MOVEOUT_REJECTED template, we would trigger it here.
            # For now, it just resets the contract to active.

        db.session.commit()
        return jsonify({'message': 'Contract status and room status updated'})
    return jsonify({'error': 'Status is required'}), 400

@admin_bp.route('/api/requests/<int:id>/status', methods=['PUT'])
@admin_required
def update_request_status(current_user, id):
    """Update request status and optionally add admin response"""
    req = Request.query.get_or_404(id)
    data = request.get_json()
    
    if 'status' in data:
        req.status = data['status']
        
        # Prepare details dict
        details_dict = {}
        if req.details:
            try:
                details_dict = json.loads(req.details)
            except:
                details_dict = {'raw': req.details}

        # Add response if provided
        if 'admin_response' in data:
            details_dict['admin_response'] = data['admin_response']
            details_dict['responded_at'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            req.details = json.dumps(details_dict)
            
        # Handle automatic actions for specific request types (Approval)
        if data.get('status') == 'done':
            if req.type == 'extension' and req.contract:
                months = details_dict.get('extension_months')
                if months:
                    # Extend the contract end date
                    req.contract.end_date = req.contract.end_date + relativedelta(months=int(months))
                    # Also update the request details to reflect it was processed
                    details_dict['processed_at'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                    req.details = json.dumps(details_dict)
            
            elif req.type == 'termination' and req.contract:
                # Update end_date to requested termination date if available
                if req.contract.termination_effective_date:
                    req.contract.end_date = req.contract.termination_effective_date
                
                # --- SMS Trigger (New) ---
                try:
                    from app.utils.sms_service import sms_service
                    from app.utils.sms_context import build_sms_context
                    context = build_sms_context(req.contract, 'MOVEOUT_APPROVED')
                    sms_service.send_sms(req.contract.id, 'MOVEOUT_APPROVED', context)
                except Exception as e:
                    print(f"SMS trigger error (MOVEOUT_APPROVED): {e}")

                today = datetime.utcnow().date()
                if req.contract.end_date <= today:
                    # Automatically update contract status to terminated
                    old_contract_status = req.contract.status
                    req.contract.status = 'terminated'
                    
                    # Sync room status
                    if req.contract.room:
                        req.contract.room.status = 'available'
                    
                    # Log contract status change
                    log_contract_status_change(
                        contract=req.contract,
                        old_status=old_contract_status,
                        new_status='terminated',
                        actor_id=current_user.id,
                        actor_type='admin',
                        source='admin_request_approval',
                        reason='Admin approved termination request (Date reached)'
                    )
                else:
                    # Future termination: The status remains 'terminate_requested' 
                    # but the end_date has been updated. tasks.py will terminate it later.
                    pass
            
        db.session.commit()
        return jsonify({'message': 'Request status updated'})
    return jsonify({'error': 'Status is required'}), 400

@admin_bp.route('/api/branches', methods=['GET'])
@admin_required
@db_retry(max_retries=3, delay=1)
def get_branches(current_user):
    """Get all branches"""
    branches = Branch.query.all()
    return jsonify([{
        'id': b.id,
        'name': b.name,
        'address': b.address,
        'facilities': b.facilities,
        'description': b.description,
        'image_url': b.image_url,
        'operating_hours': b.operating_hours,
        'contact': b.contact,
        'traffic_info': b.traffic_info,
        'parking_info': b.parking_info,
        'map_info': b.map_info,
        'images': [{'id': img.id, 'url': img.image_url} for img in b.images],
        'rooms': [{
            'id': r.id,
            'name': r.name,
            'price': r.price,
            'deposit': r.deposit,
            'status': r.status,
            'floor': r.floor,
            'room_type': r.room_type
        } for r in b.rooms]
    } for b in branches])

@admin_bp.route('/api/branches', methods=['POST'])
@admin_required
def create_branch(current_user):
    """Create new branch"""
    # Handle multipart/form-data
    name = request.form.get('name')
    address = request.form.get('address')
    facilities = request.form.get('facilities')
    description = request.form.get('description')
    operating_hours = request.form.get('operating_hours')
    contact = request.form.get('contact')
    traffic_info = request.form.get('traffic_info')
    parking_info = request.form.get('parking_info')
    map_info = request.form.get('map_info')
    
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    
    branch = Branch(
        name=name,
        address=address,
        facilities=facilities,
        description=description,
        operating_hours=operating_hours,
        contact=contact,
        traffic_info=traffic_info,
        parking_info=parking_info,
        map_info=map_info
    )
    
    # Handle image upload
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename:
            # Generate unique filename using UUID and timestamp
            file_ext = os.path.splitext(file.filename)[1]
            unique_filename = f"branch_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}{file_ext}"
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'branches')
            os.makedirs(upload_folder, exist_ok=True)
            
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)
            
            branch.image_url = f"/static/uploads/branches/{unique_filename}"
    
    db.session.add(branch)
    db.session.commit()
    return jsonify({'message': 'Branch created', 'id': branch.id}), 201

@admin_bp.route('/api/branches/<int:id>', methods=['GET'])
@admin_required
@db_retry(max_retries=3, delay=1)
def get_branch(current_user, id):
    """Get branch details with rooms"""
    branch = Branch.query.get_or_404(id)
    
    # Group rooms by floor
    rooms_by_floor = {}
    for room in branch.rooms:
        floor = room.floor or '1F'
        if floor not in rooms_by_floor:
            rooms_by_floor[floor] = []
        
        rooms_by_floor[floor].append({
            'id': room.id,
            'name': room.name,
            'room_type': room.room_type,
            'price': room.price,
            'status': room.status,
            'description': room.description,
            'floor': floor,
            'position_x': room.position_x,
            'position_y': room.position_y,
            'width': room.width,
            'height': room.height,
            'images': [{'id': img.id, 'url': img.image_url} for img in room.images]
        })
    
    # Get floor plans
    floor_plans = {}
    for fp in branch.floors:
        floor_plans[fp.floor] = fp.floor_plan_image

    return jsonify({
        'id': branch.id,
        'name': branch.name,
        'address': branch.address,
        'facilities': branch.facilities,
        'description': branch.description,
        'operating_hours': branch.operating_hours,
        'contact': branch.contact,
        'traffic_info': branch.traffic_info,
        'parking_info': branch.parking_info,
        'map_info': branch.map_info,
        'rooms': [{
            'id': r.id,
            'name': r.name,
            'room_type': r.room_type,
            'price': r.price,
            'deposit': r.deposit,
            'area': r.area,
            'description': r.description,
            'status': r.status,
            'floor': r.floor,
            'images': [{'id': img.id, 'url': img.image_url} for img in r.images]
        } for r in branch.rooms],
        'rooms_by_floor': rooms_by_floor,
        'floor_plans': floor_plans,
        'floors': [f.floor for f in branch.floors],
        'image_url': branch.image_url,
        'images': [{'id': img.id, 'url': img.image_url} for img in branch.images]
    })



@admin_bp.route('/api/branches/<int:id>', methods=['PUT'])
@admin_required
def update_branch(current_user, id):
    """Update branch"""
    branch = Branch.query.get_or_404(id)
    
    # Handle multipart/form-data
    if request.form:
        if 'name' in request.form:
            branch.name = request.form['name']
        if 'address' in request.form:
            branch.address = request.form['address']
        if 'facilities' in request.form:
            branch.facilities = request.form['facilities']
        if 'description' in request.form:
            branch.description = request.form['description']
        if 'operating_hours' in request.form:
            branch.operating_hours = request.form['operating_hours']
        if 'contact' in request.form:
            branch.contact = request.form['contact']
        if 'traffic_info' in request.form:
            branch.traffic_info = request.form['traffic_info']
        if 'parking_info' in request.form:
            branch.parking_info = request.form['parking_info']
        if 'map_info' in request.form:
            branch.map_info = request.form['map_info']
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                # Generate unique filename using UUID and timestamp
                file_ext = os.path.splitext(file.filename)[1]
                unique_filename = f"branch_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}{file_ext}"
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'branches')
                os.makedirs(upload_folder, exist_ok=True)
                
                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)
                
                branch.image_url = f"/static/uploads/branches/{unique_filename}"
    
    db.session.commit()
    return jsonify({'message': 'Branch updated'})

@admin_bp.route('/api/branches/<int:id>/images', methods=['POST'])
@admin_required
def upload_branch_images(current_user, id):
    branch = Branch.query.get_or_404(id)
    
    if 'images' not in request.files:
        return jsonify({'error': 'No images provided'}), 400
    
    files = request.files.getlist('images')
    uploaded_images = []
    
    for file in files:
        if file and file.filename:
            filename = secure_filename(f"branch_{id}_{file.filename}")
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'branches')
            os.makedirs(upload_folder, exist_ok=True)
            
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            
            image_url = f"/static/uploads/branches/{filename}"
            
            # Create BranchImage record
            branch_image = BranchImage(branch_id=branch.id, image_url=image_url)
            db.session.add(branch_image)
            uploaded_images.append(image_url)
            
            # If it's the first image and branch has no main image, set it
            if not branch.image_url:
                branch.image_url = image_url
    
    db.session.commit()
    return jsonify({'message': 'Images uploaded successfully', 'images': uploaded_images}), 201

@admin_bp.route('/api/branches/<int:branch_id>/images/<int:image_id>', methods=['DELETE'])
@admin_required
def delete_branch_image(current_user, branch_id, image_id):
    image = BranchImage.query.filter_by(id=image_id, branch_id=branch_id).first_or_404()
    
    # Optional: Delete file from filesystem
    try:
        file_path = os.path.join(current_app.root_path, image.image_url.lstrip('/'))
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error deleting file: {e}")
    
    db.session.delete(image)
    db.session.commit()
    return jsonify({'message': 'Image deleted successfully'})

@admin_bp.route('/api/branches/<int:id>', methods=['DELETE'])
@admin_required
def delete_branch(current_user, id):
    """Delete branch"""
    branch = Branch.query.get_or_404(id)
    force = request.args.get('force', 'false').lower() == 'true'
    
    # Convert to list to get the count
    rooms = list(branch.rooms)
    room_count = len(rooms)
    
    # If branch has rooms and force is not true, return room count info
    if room_count > 0 and not force:
        return jsonify({
            'error': 'Branch has rooms',
            'room_count': room_count
        }), 400
    
    # Delete all rooms first if force is true
    if force and room_count > 0:
        for room in rooms:
            db.session.delete(room)
    
    db.session.delete(branch)
    db.session.commit()
    return jsonify({'message': 'Branch deleted'})

@admin_bp.route('/api/rooms', methods=['POST'])
@admin_required
def create_room(current_user):
    """Create new room"""
    data = request.get_json()
    room = Room(
        branch_id=data['branch_id'],
        name=data['name'],
        room_type=data.get('room_type', 'monthly'),
        price=data['price'],
        deposit=data.get('deposit'),
        area=data.get('area'),
        description=data.get('description'),
        floor=data.get('floor', '1F'),
        # Default coordinates
        position_x=0,
        position_y=0,
        width=10,
        height=10
    )
    db.session.add(room)
    db.session.commit()
    return jsonify({'message': 'Room created', 'id': room.id}), 201

@admin_bp.route('/api/rooms/<int:id>', methods=['PUT'])
@admin_required
def update_room(current_user, id):
    """Update room"""
    room = Room.query.get_or_404(id)
    data = request.get_json()
    
    if 'floor' in data:
        room.floor = data['floor']
    if 'name' in data:
        room.name = data['name']
    if 'room_type' in data:
        room.room_type = data['room_type']
    if 'price' in data:
        room.price = data['price']
    if 'deposit' in data:
        room.deposit = data['deposit']
    if 'area' in data:
        room.area = data['area']
    if 'description' in data:
        room.description = data['description']
    
    db.session.commit()
    return jsonify({'message': 'Room updated', 'id': room.id})

@admin_bp.route('/api/rooms/<int:id>', methods=['DELETE'])
@admin_required
def delete_room(current_user, id):
    """Delete room"""
    room = Room.query.get_or_404(id)
    
    # Check if room has active contracts
    active_contracts = Contract.query.filter_by(
        room_id=id,
        status='active'
    ).count()
    
    if active_contracts > 0:
        return jsonify({
            'error': '활성 계약이 있는 방은 삭제할 수 없습니다',
            'active_contracts': active_contracts
        }), 400
    
    db.session.delete(room)
    db.session.commit()
    return jsonify({'message': 'Room deleted'})

@admin_bp.route('/api/branches/<int:id>/floors/<floor>/plan', methods=['POST'])
@admin_required
def upload_floor_plan(current_user, id, floor):
    """Upload floor plan image"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filename = secure_filename(f"branch_{id}_{floor}_{file.filename}")
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'floor_plans')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        image_url = f"/static/uploads/floor_plans/{filename}"
        
        # Update or create BranchFloor
        branch_floor = BranchFloor.query.filter_by(branch_id=id, floor=floor).first()
        if not branch_floor:
            branch_floor = BranchFloor(branch_id=id, floor=floor)
            db.session.add(branch_floor)
        
        branch_floor.floor_plan_image = image_url
        db.session.commit()
        
        return jsonify({'message': 'Floor plan uploaded', 'image_url': image_url})

@admin_bp.route('/api/branches/<int:id>/floors/<floor>/positions', methods=['PUT'])
@admin_required
def update_room_positions(current_user, id, floor):
    """Update room positions for a floor"""
    data = request.get_json()
    positions = data.get('positions', [])
    
    for pos in positions:
        room = Room.query.get(pos['id'])
        if room and room.branch_id == id:
            room.position_x = pos.get('x')
            room.position_y = pos.get('y')
            room.width = pos.get('w')
            room.height = pos.get('h')
            
    db.session.commit()
    return jsonify({'message': 'Positions updated'})

@admin_bp.route('/api/branches/<int:id>/floors', methods=['POST'])
@admin_required
def add_branch_floor(current_user, id):
    """Add a floor to a branch"""
    data = request.get_json()
    floor_name = data.get('floor')
    
    if not floor_name:
        return jsonify({'error': 'Floor name is required'}), 400
        
    # Check if floor already exists
    existing = BranchFloor.query.filter_by(branch_id=id, floor=floor_name).first()
    if existing:
        return jsonify({'error': 'Floor already exists'}), 400
        
    branch_floor = BranchFloor(branch_id=id, floor=floor_name)
    db.session.add(branch_floor)
    db.session.commit()
    
    return jsonify({'message': 'Floor added', 'floor': floor_name}), 201

@admin_bp.route('/api/branches/<int:id>/floors/<floor>', methods=['DELETE'])
@admin_required
def delete_branch_floor(current_user, id, floor):
    """Delete a floor from a branch"""
    branch_floor = BranchFloor.query.filter_by(branch_id=id, floor=floor).first()
    
    if not branch_floor:
        return jsonify({'error': 'Floor not found'}), 404
        
    # Check if there are rooms on this floor
    rooms_on_floor = Room.query.filter_by(branch_id=id, floor=floor).count()
    if rooms_on_floor > 0:
        return jsonify({'error': 'Cannot delete floor with existing rooms'}), 400
        
    db.session.delete(branch_floor)
    db.session.commit()
    
    return jsonify({'message': 'Floor deleted'})

@admin_bp.route('/api/rooms/<int:id>/images', methods=['POST'])
@admin_required
def upload_room_images(current_user, id):
    """Upload multiple images for a room"""
    room = Room.query.get_or_404(id)
    
    if 'images' not in request.files:
        return jsonify({'error': 'No images provided'}), 400
    
    files = request.files.getlist('images')
    uploaded_images = []
    
    for file in files:
        if file and file.filename:
            filename = secure_filename(f"room_{id}_{file.filename}")
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'rooms')
            os.makedirs(upload_folder, exist_ok=True)
            
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            
            image_url = f"/static/uploads/rooms/{filename}"
            room_image = RoomImage(room_id=id, image_url=image_url)
            db.session.add(room_image)
            uploaded_images.append({'url': image_url})
    
    db.session.commit()
    return jsonify({'message': 'Images uploaded', 'images': uploaded_images}), 201

@admin_bp.route('/api/rooms/<int:room_id>/images/<int:image_id>', methods=['DELETE'])
@admin_required
def delete_room_image(current_user, room_id, image_id):
    """Delete a room image"""
    room_image = RoomImage.query.filter_by(id=image_id, room_id=room_id).first_or_404()
    
    # Optionally delete the file from disk
    try:
        if room_image.image_url:
            file_path = os.path.join(current_app.root_path, room_image.image_url.lstrip('/'))
            if os.path.exists(file_path):
                os.remove(file_path)
    except Exception as e:
        print(f"Error deleting file: {e}")
    
    db.session.delete(room_image)
    db.session.commit()
    return jsonify({'message': 'Image deleted'})

# ============================================================
# 미매핑 계약 관리 API
# ============================================================

@admin_bp.route('/api/contracts/unmapped', methods=['GET'])
@admin_required
@db_retry(max_retries=3, delay=1)
def get_unmapped_contracts(current_user):
    """모든 미매핑 계약 조회"""
    unmapped = ContractMappingService.get_all_unmapped_contracts()
    
    return jsonify([{
        'id': c.id,
        'temp_user_name': c.temp_user_name,
        'temp_user_phone': c.temp_user_phone,
        'temp_user_email': c.temp_user_email,
        'room_name': c.room.name if c.room else '알 수 없음',
        'branch_name': c.room.branch.name if c.room and c.room.branch else '알 수 없음',
        'deposit': c.room.deposit if c.room else 0,
        'price': c.room.price if c.room else 0,
        'start_date': c.start_date.strftime('%Y-%m-%d'),
        'end_date': c.end_date.strftime('%Y-%m-%d'),
        'status': c.status,
        'created_at': c.created_at.strftime('%Y-%m-%d %H:%M') if c.created_at else ''
    } for c in unmapped])

@admin_bp.route('/api/contracts/unmapped', methods=['POST'])
@admin_required
def create_unmapped_contract(current_user):
    """미매핑 계약 생성 (회원가입 전 계약 데이터 입력)"""
    data = request.get_json()
    
    # 필수 필드 확인
    required_fields = ['room_id', 'temp_user_phone', 'start_date', 'end_date']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    # 방 존재 확인
    room = Room.query.get(data['room_id'])
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    
    # 계약 생성 (user_id는 None)
    contract = Contract(
        user_id=None,  # 미매핑 상태
        room_id=data['room_id'],
        temp_user_name=data.get('temp_user_name'),
        temp_user_phone=data['temp_user_phone'],
        temp_user_email=data.get('temp_user_email'),
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
        end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date(),
        status=data.get('status', 'active'),  # 기본값: active
        months=data.get('months'),
        total_price=data.get('total_price')
    )
    
    db.session.add(contract)
    db.session.commit()
    
    return jsonify({
        'message': '미매핑 계약이 생성되었습니다',
        'id': contract.id,
        'temp_user_phone': contract.temp_user_phone
    }), 201

@admin_bp.route('/api/contracts/<int:contract_id>/map/<int:user_id>', methods=['POST'])
@admin_required
def manual_map_contract(current_user, contract_id, user_id):
    """관리자가 수동으로 계약을 사용자에게 매핑"""
    success = ContractMappingService.manual_map_contract(contract_id, user_id)
    
    if success:
        return jsonify({'message': '계약이 성공적으로 매핑되었습니다'})
    else:
        return jsonify({'error': '계약 또는 사용자를 찾을 수 없습니다'}), 404

@admin_bp.route('/api/contracts/<int:contract_id>/search-user', methods=['GET'])
@admin_required
def search_user_for_contract(current_user, contract_id):
    """계약에 매핑 가능한 사용자 검색"""
    contract = Contract.query.get_or_404(contract_id)
    
    if not contract.is_unmapped:
        return jsonify({'error': '이미 매핑된 계약입니다'}), 400
    
    # 전화번호나 이메일로 사용자 검색
    matching_users = []
    
    if contract.temp_user_phone:
        users = User.query.filter_by(phone=contract.temp_user_phone).all()
        matching_users.extend(users)
    
    if contract.temp_user_email:
        users = User.query.filter_by(email=contract.temp_user_email).all()
        matching_users.extend(users)
    
    # 중복 제거
    unique_users = {user.id: user for user in matching_users}.values()
    
    return jsonify([{
        'id': u.id,
        'name': u.name,
        'email': u.email,
        'phone': u.phone,
        'created_at': u.created_at.strftime('%Y-%m-%d %H:%M') if u.created_at else ''
    } for u in unique_users])


# ============================================================
# 회원 관리 API
# ============================================================

@admin_bp.route('/api/users', methods=['GET'])
@admin_required
@db_retry(max_retries=3, delay=1)
def get_users(current_user):
    """모든 회원 조회"""
    users = User.query.all()
    result = []
    
    for u in users:
        active_branch_ids = [c.room.branch_id for c in u.contracts if c.status == 'active' and c.room]
        result.append({
            'id': u.id,
            'name': u.name,
            'email': u.email,
            'phone': u.phone,
            'kakao_id': u.kakao_id,
            'role': u.role,
            'onboarding_status': u.onboarding_status,
            'created_at': u.created_at.strftime('%Y-%m-%d %H:%M') if u.created_at else '',
            'contract_count': len(active_branch_ids),
            'branch_ids': list(set(active_branch_ids))
        })
    
    return jsonify(result)

@admin_bp.route('/api/users', methods=['POST'])
@admin_required
def create_user(current_user):
    """회원 등록"""
    data = request.get_json()
    
    # Validation
    if not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'error': '이름, 이메일, 비밀번호는 필수입니다.'}), 400
        
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': '이미 존재하는 이메일입니다.'}), 400
        
    new_user = User(
        email=data['email'],
        name=data['name'],
        phone=data.get('phone', ''),
        role=data.get('role', 'user'),
        onboarding_status='new_user_done' # Admin created users are assumed to be "done"
    )
    new_user.set_password(data['password'])
    
    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': '이미 사용 중인 전화번호이거나 중복된 데이터가 존재합니다.'}), 400
    
    return jsonify({
        'message': 'User created',
        'id': new_user.id
    }), 201

@admin_bp.route('/api/users/<int:id>', methods=['PUT'])
@admin_required
def update_user(current_user, id):
    """회원 정보 수정"""
    user = User.query.get_or_404(id)
    data = request.get_json()
    
    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        user.email = data['email']
    if 'phone' in data:
        user.phone = data['phone']
    if 'role' in data:
        user.role = data['role']
    if 'onboarding_status' in data:
        user.onboarding_status = data['onboarding_status']
        
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': '이미 사용 중인 전화번호이거나 중복된 데이터가 존재합니다.'}), 400
        
    return jsonify({'message': 'User updated'})

@admin_bp.route('/api/users/<int:id>', methods=['DELETE'])
@admin_required
def delete_user(current_user, id):
    """회원 삭제"""
    user = User.query.get_or_404(id)
    
    # Check dependencies (active contracts?)
    active_contracts = user.contracts.filter(Contract.status == 'active').count()
    if active_contracts > 0:
        return jsonify({'error': '활성 계약이 있는 회원은 삭제할 수 없습니다.', 'active_contracts': active_contracts}), 400
        
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'})

@admin_bp.route('/api/coupons', methods=['GET'])
@admin_required
def get_coupons(current_user):
    """Get all coupons"""
    coupons = Coupon.query.order_by(Coupon.created_at.desc()).all()
    results = []
    for c in coupons:
        results.append({
            'id': c.id,
            'code': c.code,
            'discount_type': c.discount_type,
            'discount_value': c.discount_value,
            'discount_cycle': c.discount_cycle,
            'stack_policy': c.stack_policy,
            'valid_from': c.valid_from.strftime('%Y-%m-%d'),
            'valid_until': c.valid_until.strftime('%Y-%m-%d'),
            'min_months': c.min_months,
            'usage_limit': c.usage_limit,
            'used_count': c.used_count,
            'is_active': c.is_active,
            'created_at': c.created_at.strftime('%Y-%m-%d %H:%M')
        })
    return jsonify(results)

@admin_bp.route('/api/coupons', methods=['POST'])
@admin_required
def create_coupon(current_user):
    """Create new coupon"""
    data = request.get_json()
    
    # Validation
    required_fields = ['code', 'discount_type', 'discount_value', 'valid_from', 'valid_until']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
            
    # Check duplicate code
    if Coupon.query.filter_by(code=data['code']).first():
        return jsonify({'error': 'Coupon code already exists'}), 400
        
    try:
        valid_from = datetime.strptime(data['valid_from'], '%Y-%m-%d').date()
        valid_until = datetime.strptime(data['valid_until'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
        
    coupon = Coupon(
        code=data['code'],
        discount_type=data['discount_type'],
        discount_value=int(data['discount_value']),
        discount_cycle=data.get('discount_cycle', 'once'),
        stack_policy=data.get('stack_policy', 'STACK_WITH_MONTHLY_PROMO'),
        valid_from=valid_from,
        valid_until=valid_until,
        min_months=int(data.get('min_months')) if data.get('min_months') else None,
        usage_limit=int(data.get('usage_limit')) if data.get('usage_limit') else None,
        is_active=data.get('is_active', True)
    )
    
    db.session.add(coupon)
    db.session.commit()
    
    return jsonify({'message': 'Coupon created', 'id': coupon.id}), 201

@admin_bp.route('/api/coupons/<int:id>', methods=['DELETE'])
@admin_required
def delete_coupon(current_user, id):
    """Delete (Deactivate) coupon"""
    coupon = Coupon.query.get_or_404(id)
    if coupon.used_count > 0:
        return jsonify({'error': '이미 사용된 쿠폰은 삭제할 수 없습니다.'}), 400

    db.session.delete(coupon)
    db.session.commit()
    return jsonify({'message': 'Coupon deleted'})


@admin_bp.route('/api/calendar/events', methods=['GET'])
@admin_required
def get_calendar_events(current_user):
    """
    Get calendar events for admin dashboard
    Returns JSON array of events:
    - Time-based reservations: displayed as time blocks
    - Monthly payment days: displayed as all-day events
    """
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    event_type = request.args.get('type', 'all') # 'all', 'time', 'monthly'
    
    if not start_str or not end_str:
        return jsonify([])

    try:
        # FullCalendar sends ISO format (often with time, e.g., 2023-10-01T00:00:00-05:00)
        # We only care about the date part for filtering range
        start_date = datetime.fromisoformat(start_str.split('T')[0]).date()
        end_date = datetime.fromisoformat(end_str.split('T')[0]).date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    events = []

    # 1. Time-based Contracts (Reservations)
    if event_type in ['all', 'time']:
        time_contracts = Contract.query.join(Contract.room).filter(
            Room.room_type == 'time_based',
            Contract.start_date >= start_date,
            Contract.end_date <= end_date
        ).all()

        for c in time_contracts:
            user_info = c.get_user_info()
            user_name = user_info['name'] or 'Unknown'
            
            # Combine date and time for FullCalendar
            start_dt = f"{c.start_date}T{c.start_time}"
            end_dt = f"{c.end_date}T{c.end_time}"
            
            branch_name = c.room.branch.name if c.room and c.room.branch else 'Unknown'
            events.append({
                'title': f'[{branch_name}] {user_name} ({c.start_time}~{c.end_time})',
                'start': start_dt,
                'end': end_dt,
                'color': '#3b82f6', # Blue for time-based
                'extendedProps': {
                    'contract_id': c.id,
                    'amount': c.price,
                    'type': 'time',
                    'room_name': c.room.name,
                    'branch_name': branch_name
                }
            })

    # 2. Monthly Contracts (Payment Days)
    if event_type in ['all', 'monthly']:
        monthly_contracts = Contract.query.join(Contract.room).filter(
            Room.room_type != 'time_based',
            Contract.status == 'active',
            # Overlap check: Contract must be active during the requested window
            Contract.start_date <= end_date,
            Contract.end_date >= start_date
        ).all()

        for c in monthly_contracts:
            if not c.payment_day:
                continue
                
            # Iterate through months in the requested range to generate payment events
            # Start iteration from the later of (range start, contract start)
            current_iter_date = max(start_date, c.start_date)
            # End iteration at the earlier of (range end, contract end)
            end_iter_date = min(end_date, c.end_date)
            
            # Normalize to the first of the month to start iteration loop cleanly
            iter_month = current_iter_date.replace(day=1)
            
            while iter_month <= end_iter_date:
                # Calculate payment date for this month
                # Handle short months (e.g., payment day 31 in Feb) -> standard approach is skip or last day.
                # Here we will try to use the exact day. If invalid (e.g. Feb 30), we skip for simplicity or clamp.
                # Creates a robust "last day" logic:
                
                try:
                    payment_date = iter_month.replace(day=c.payment_day)
                except ValueError:
                    # If day is out of range for this month, set to last day of month
                    # (e.g. payment day 31 in Feb -> Feb 28/29)
                    next_month = iter_month + relativedelta(months=1)
                    last_day_of_month = next_month - timedelta(days=1)
                    payment_date = last_day_of_month
                
                # Check if this specific payment date is within the contract period AND requested range
                if (payment_date >= c.start_date and 
                    payment_date <= c.end_date and 
                    payment_date >= start_date and 
                    payment_date <= end_date):
                    
                    user_info = c.get_user_info()
                    user_name = user_info['name'] or 'Unknown'
                    
                    branch_name = c.room.branch.name if c.room and c.room.branch else 'Unknown'
                    events.append({
                        'title': f'[{branch_name}] 결제: {user_name} ({c.room.name})',
                        'start': payment_date.isoformat(),
                        'allDay': True,
                        'color': '#10b981', # Green for monthly payment
                        'extendedProps': {
                            'contract_id': c.id,
                            'amount': c.price,
                            'type': 'monthly',
                            'room_name': c.room.name,
                            'branch_name': branch_name
                        }
                    })
                
                # Move to next month
                iter_month += relativedelta(months=1)
            
    return jsonify(events)




# --- SMS Management APIs ---

@admin_bp.route('/api/sms/templates', methods=['GET'])
@admin_required
def get_sms_templates(current_user):
    """GET all SMS templates"""
    templates = SmsTemplate.query.all()
    
    # Pre-calculate byte length using dummy data
    dummy_context = get_dummy_context()
    
    results = []
    for t in templates:
        # Render with dummy data
        rendered, _ = sms_service.render_template(t.content, dummy_context)
        
        # Calculate bytes (EUC-KR estimation: Korean=2, ASCII=1)
        # Python len(encode('euc-kr')) is accurate for this.
        try:
            # Aligo uses EUC-KR. 
            predicted_bytes = len(rendered.encode('euc-kr'))
        except UnicodeEncodeError:
            # Fallback for chars not in EUC-KR (e.g. some emojis) -> use utf-8 length or estimate
            predicted_bytes = len(rendered.encode('utf-8'))
            
        predicted_type = 'LMS' if predicted_bytes > 90 else 'SMS'

        results.append({
            'id': t.id,
            'type': t.type,
            'title': t.title,
            'content': t.content,
            'is_active': t.is_active,
            'schedule_offset': t.schedule_offset,
            'allowed_variables': SMS_VARIABLE_SCHEMA.get(t.type, []),
            'updated_at': t.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'predicted_bytes': predicted_bytes,
            'predicted_type': predicted_type
        })
        
    return jsonify(results)

@admin_bp.route('/api/sms/templates/<int:id>', methods=['PUT'])
@admin_required
def update_sms_template(current_user, id):
    """Update SMS template"""
    template = SmsTemplate.query.get_or_404(id)
    data = request.get_json()
    
    if 'title' in data:
        template.title = data['title']
    if 'content' in data:
        template.content = data['content']
    if 'is_active' in data:
        template.is_active = data['is_active']
    if 'schedule_offset' in data:
        template.schedule_offset = int(data['schedule_offset'])
        
    template.updated_by_admin_id = current_user.id
    template.updated_reason = data.get('reason')
    
    db.session.commit()
    return jsonify({'message': 'Template updated'})

@admin_bp.route('/api/sms/logs', methods=['GET'])
@admin_required
def get_sms_logs(current_user):
    """GET SMS logs with filtering"""
    status_filter = request.args.get('status')
    query = SmsLog.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
        
    logs = query.order_by(SmsLog.sent_at.desc()).limit(100).all()
    
    return jsonify([{
        'id': l.id,
        'contract_id': l.contract_id,
        'user_name': l.contract.get_user_info()['name'] if l.contract else 'N/A',
        'type': l.type,
        'content': l.content_snapshot,
        'status': l.status,
        'sent_at': l.sent_at.strftime('%m-%d %H:%M'),
        'error_message': l.error_message
    } for l in logs])

@admin_bp.route('/api/sms/preview', methods=['POST'])
@admin_required
def preview_sms(current_user):
    """Preview SMS rendering with dummy data"""
    data = request.get_json()
    content = data.get('content', '')
    msg_type = data.get('type', 'CONTRACT_APPLIED')
    contract_id = data.get('contract_id')
    
    context = {}
    if contract_id:
        contract = Contract.query.get(contract_id)
        if contract:
            context = build_sms_context(contract, msg_type)
            
    if not context:
        # Dummy context based on schema
        context = get_dummy_context()
    
    from app.utils.sms_service import sms_service
    rendered, missing = sms_service.render_template(content, context)
    
    return jsonify({
        'rendered': rendered,
        'missing': missing
    })

@admin_bp.route('/api/sms/manual', methods=['POST'])
@admin_required
def send_manual_sms(current_user):
    """Send manual SMS to a contract user"""
    data = request.get_json()
    contract_id = data.get('contract_id')
    msg_type = data.get('type', 'MANUAL')
    content = data.get('content') # Optional override or required for MANUAL

    if not contract_id:
        return jsonify({'error': 'Contract ID required'}), 400

    contract = Contract.query.get_or_404(contract_id)
    
    # 1. Build Context
    context = build_sms_context(contract, msg_type)
    
    # 2. Send SMS (Force Send = True)
    success, message = sms_service.send_sms(
        contract_id=contract.id,
        msg_type=msg_type,
        context=context,
        content_override=content,
        force_send=True
    )
    
    if success:
        return jsonify({'message': 'Sent successfully', 'log': message})
    else:
        return jsonify({'error': message}), 500

@admin_bp.route('/api/contracts/search', methods=['GET'])
@admin_required
def search_contracts(current_user):
    """Search contracts by user name or phone"""
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])

    # Mapped contracts (Active Only for now, or all?)
    # User might want to send SMS to 'terminated' users too (e.g. deposit refund).
    # So let's include terminated.
    mapped = Contract.query.join(User).filter(
        (User.name.ilike(f'%{q}%')) | (User.phone.ilike(f'%{q}%'))
    ).limit(20).all()

    # Unmapped contracts
    unmapped = Contract.query.filter(
        Contract.user_id == None,
        (Contract.temp_user_name.ilike(f'%{q}%')) | (Contract.temp_user_phone.ilike(f'%{q}%'))
    ).limit(20).all()

    results = []
    # Deduplicate by ID just in case, though unlikely
    seen_ids = set()
    
    for c in mapped + unmapped:
        if c.id in seen_ids:
            continue
        seen_ids.add(c.id)
        
        user_info = c.get_user_info()
        results.append({
            'id': c.id,
            'user_name': user_info['name'],
            'user_phone': user_info['phone'],
            'room_name': c.room.name if c.room else 'N/A',
            'branch_name': c.room.branch.name if c.room and c.room.branch else 'N/A',
            'status': c.status,
            'start_date': c.start_date.strftime('%Y-%m-%d'),
            'end_date': c.end_date.strftime('%Y-%m-%d')
        })
    
    return jsonify(results[:20])

# ============================================================
# 특정 월 추가 할인 (Custom Discount) API
# ============================================================
from app.models.custom_discount import CustomDiscount

@admin_bp.route('/api/contracts/<int:contract_id>/custom-discounts', methods=['GET'])
@admin_required
def get_custom_discounts(current_user, contract_id):
    """특정 계약의 월별 추가 할인 내역 조회"""
    discounts = CustomDiscount.query.filter_by(contract_id=contract_id).order_by(CustomDiscount.target_month.desc()).all()
    return jsonify([{
        'id': d.id,
        'target_month': d.target_month,
        'amount': d.amount,
        'reason': d.reason,
        'admin_id': d.admin_id,
        'created_at': d.created_at.strftime('%Y-%m-%d %H:%M') if d.created_at else ''
    } for d in discounts])

@admin_bp.route('/api/contracts/<int:contract_id>/custom-discounts', methods=['POST'])
@admin_required
def save_custom_discount(current_user, contract_id):
    """특정 계약에 지정 월 할인 추가 또는 수정"""
    contract = Contract.query.get_or_404(contract_id)
    data = request.get_json()
    
    target_month = data.get('target_month') # YYYY-MM
    amount = data.get('amount', 0)
    reason = data.get('reason', '')
    
    if not target_month or not isinstance(amount, int) or amount < 0:
        return jsonify({'error': '유효한 대상 월(YYYY-MM)과 0 이상의 할인 금액을 입력해주세요.'}), 400
        
    discount = CustomDiscount.query.filter_by(contract_id=contract_id, target_month=target_month).first()
    
    if discount:
        discount.amount = amount
        discount.reason = reason
        discount.admin_id = current_user.id
        message = '할인 내역이 수정되었습니다.'
    else:
        discount = CustomDiscount(
            contract_id=contract_id,
            target_month=target_month,
            amount=amount,
            reason=reason,
            admin_id=current_user.id
        )
        db.session.add(discount)
        message = '할인 내역이 추가되었습니다.'
        
    db.session.commit()
    return jsonify({'message': message, 'id': discount.id})

@admin_bp.route('/api/contracts/<int:contract_id>/custom-discounts/<target_month>', methods=['DELETE'])
@admin_required
def delete_custom_discount(current_user, contract_id, target_month):
    """지정 월 할인 내역 삭제"""
    discount = CustomDiscount.query.filter_by(contract_id=contract_id, target_month=target_month).first_or_404()
    
    db.session.delete(discount)
    db.session.commit()
    return jsonify({'message': '할인 내역이 삭제되었습니다.'})

