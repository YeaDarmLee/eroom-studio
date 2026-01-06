from flask import Blueprint, jsonify
from app.models.branch import Branch, Room
from app.utils.db_utils import db_retry

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
        'price': room.price,
        'status': room.status,
        'description': room.description,
        'images': [{'id': img.id, 'url': img.image_url} for img in room.images]
    })
