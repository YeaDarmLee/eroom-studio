from flask import Blueprint, jsonify, request
from app.models.branch import Branch, Room
from app.models.contract import Contract
from app.utils.db_utils import db_retry
from datetime import datetime

public_bp = Blueprint('public', __name__, url_prefix='/api/public')

@public_bp.route('/branches', methods=['GET'])
@db_retry(max_retries=3, delay=1)
def get_branches():
    branches = Branch.query.all()
    result = []
    for branch in branches:
        result.append({
            'id': branch.id,
            'name': branch.name,
            'description': branch.description,
            'address': branch.address,
            'facilities': branch.facilities,
            'image_url': branch.image_url
        })
    return jsonify(result)

@public_bp.route('/branches/<int:branch_id>', methods=['GET'])
@db_retry(max_retries=3, delay=1)
def get_branch(branch_id):
    branch = Branch.query.get_or_404(branch_id)
    
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
            'deposit': room.deposit,
            'status': room.status,
            'next_available_date': room.get_next_available_date().isoformat() if room.get_next_available_date() else None,
            'description': room.description,
            'area': room.area,
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
        'description': branch.description,
        'address': branch.address,
        'facilities': branch.facilities,
        'map_info': branch.map_info,
        'rooms_by_floor': rooms_by_floor,
        'floor_plans': floor_plans
    })

@public_bp.route('/branches/<int:branch_id>/rooms', methods=['GET'])
@db_retry(max_retries=3, delay=1)
def get_branch_rooms(branch_id):
    branch = Branch.query.get_or_404(branch_id)
    rooms = branch.rooms.all()
    result = []
    for room in rooms:
        result.append({
            'id': room.id,
            'name': room.name,
            'price': room.price,
            'status': room.status,
            'description': room.description,
            'images': [{'id': img.id, 'url': img.image_url} for img in room.images]
        })
    return jsonify(result)

@public_bp.route('/rooms/<int:room_id>', methods=['GET'])
@db_retry(max_retries=3, delay=1)
def get_room(room_id):
    room = Room.query.get_or_404(room_id)
    return jsonify({
        'id': room.id,
        'branch_id': room.branch_id,
        'name': room.name,
        'room_type': room.room_type,
        'price': room.price,
        'deposit': room.deposit,
        'status': room.status,
        'description': room.description,
        'next_available_date': room.get_next_available_date().isoformat() if room.get_next_available_date() else None,
        'images': [{'id': img.id, 'url': img.image_url} for img in room.images]
    })

@public_bp.route('/rooms/<int:room_id>/reservations', methods=['GET'])
@db_retry(max_retries=3, delay=1)
def get_room_reservations(room_id):
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'error': 'Date is required'}), 400
        
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
        
    # Get all non-cancelled reservations for this room on this date
    blocking_statuses = ['requested', 'approved', 'active', 'extend_requested']
    
    reservations = Contract.query.filter(
        Contract.room_id == room_id,
        Contract.start_date == target_date,
        Contract.status.in_(blocking_statuses)
    ).all()
    
    result = []
    for res in reservations:
        result.append({
            'start_time': res.start_time,
            'end_time': res.end_time,
            'status': res.status
        })
        
    return jsonify(result)

@public_bp.route('/branches/<string:branch_name>/rooms-status', methods=['GET'])
@db_retry(max_retries=3, delay=1)
def get_branch_rooms_status(branch_name):
    # 지점 영문명 -> DB 지점명 매핑
    mapping = {
        "samsung": ["삼성점", "삼성", "samsung"],
        "hongdae": ["홍대점", "홍대", "hongdae"],
        "incheon": ["인천점", "인천", "incheon"],
        "mokdong": ["목동점", "목동", "mokdong"],
        "bongcheon": ["봉천점", "봉천", "bongcheon"],
        "bucheon": ["부천점", "부천", "bucheon"]
    }
    
    branch = None
    search_names = mapping.get(branch_name.lower())
    if search_names:
        for name in search_names:
            branch = Branch.query.filter(Branch.name.like(f"%{name}%")).first()
            if branch:
                break
                
    if not branch:
        branch = Branch.query.filter(Branch.name.like(f"%{branch_name}%")).first()
        
    if not branch:
        return jsonify({'error': 'Branch not found'}), 404
        
    # 공실 상태인 방 필터링
    available_rooms = []
    valid_rooms = [r for r in branch.rooms.all() if r.room_type not in ['time_based', 'manager']]
    
    for room in valid_rooms:
        if room.status == 'available':
            # 평수 계산 (area가 제곱미터인 경우 평수로 환산)
            area_pyung = (room.area / 3.3058) if room.area else 0.0
            available_rooms.append({
                'floor': room.floor or '',
                'name': room.name,
                'area_pyung': area_pyung,
                'price': room.price or 0,
                'description': room.description or ''
            })
            
    is_fully_occupied = len(available_rooms) == 0
    next_available_date_str = None
    
    if is_fully_occupied:
        # 모든 유효한 방 중 가장 빠른 입실 가능 예정일 계산
        dates = []
        for room in valid_rooms:
            d = room.get_next_available_date()
            if d:
                dates.append(d)
        if dates:
            next_available_date_str = min(dates).strftime('%Y-%m-%d')
        else:
            # 기본값 설정
            from datetime import date, timedelta
            next_available_date_str = (date.today() + timedelta(days=14)).strftime('%Y-%m-%d')
            
    return jsonify({
        'branch_name': branch.name,
        'available_rooms': available_rooms,
        'is_fully_occupied': is_fully_occupied,
        'next_available_date': next_available_date_str
    })

