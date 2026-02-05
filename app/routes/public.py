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
    
    # Get services grouped by type
    common_services = []
    specialized_services = []
    
    for service in branch.services:
        service_data = {
            'id': service.id,
            'name': service.name,
            'description': service.description,
            'icon': service.icon
        }
        
        if service.service_type == 'common':
            common_services.append(service_data)
        elif service.service_type == 'specialized':
            specialized_services.append(service_data)
    
    return jsonify({
        'id': branch.id,
        'name': branch.name,
        'description': branch.description,
        'address': branch.address,
        'facilities': branch.facilities,
        'map_info': branch.map_info,
        'rooms_by_floor': rooms_by_floor,
        'floor_plans': floor_plans,
        'common_services': common_services,
        'specialized_services': specialized_services
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
