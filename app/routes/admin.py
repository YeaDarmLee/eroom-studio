from flask import Blueprint, request, jsonify, current_app, render_template
from app.models import db
from app.models.user import User
from app.models.branch import Branch, Room, BranchFloor
from app.models.contract import Contract
from app.models.request import Request
from app.routes.auth import admin_required
import os
from werkzeug.utils import secure_filename

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@admin_required
def dashboard(current_user):
    """Admin dashboard page"""
    return render_template('admin/dashboard.html')

@admin_bp.route('/api/contracts', methods=['GET'])
@admin_required
def get_contracts(current_user):
    """Get all contracts"""
    contracts = Contract.query.all()
    return jsonify([{
        'id': c.id,
        'user_name': c.user.name if c.user else 'Unknown',
        'room_name': c.room.name if c.room else 'Unknown',
        'start_date': c.start_date.strftime('%Y-%m-%d'),
        'end_date': c.end_date.strftime('%Y-%m-%d'),
        'status': c.status
    } for c in contracts])

@admin_bp.route('/api/requests', methods=['GET'])
@admin_required
def get_requests(current_user):
    """Get all requests"""
    requests = Request.query.all()
    return jsonify([{
        'id': r.id,
        'user_name': r.user.name,
        'type': r.type,
        'status': r.status,
        'created_at': r.created_at.strftime('%Y-%m-%d')
    } for r in requests])

@admin_bp.route('/api/contracts/<int:id>/status', methods=['PUT'])
@admin_required
def update_contract_status(current_user, id):
    """Update contract status"""
    contract = Contract.query.get_or_404(id)
    data = request.get_json()
    
    if 'status' in data:
        contract.status = data['status']
        db.session.commit()
        return jsonify({'message': 'Contract status updated'})
    return jsonify({'error': 'Status is required'}), 400

@admin_bp.route('/api/requests/<int:id>/status', methods=['PUT'])
@admin_required
def update_request_status(current_user, id):
    """Update request status"""
    req = Request.query.get_or_404(id)
    data = request.get_json()
    
    if 'status' in data:
        req.status = data['status']
        db.session.commit()
        return jsonify({'message': 'Request status updated'})
    return jsonify({'error': 'Status is required'}), 400

@admin_bp.route('/api/branches', methods=['GET'])
@admin_required
def get_branches(current_user):
    """Get all branches"""
    branches = Branch.query.all()
    return jsonify([{
        'id': b.id,
        'name': b.name,
        'address': b.address,
        'room_count': b.rooms.count()
    } for b in branches])

@admin_bp.route('/api/branches', methods=['POST'])
@admin_required
def create_branch(current_user):
    """Create new branch"""
    data = request.get_json()
    branch = Branch(
        name=data['name'],
        address=data.get('address'),
        facilities=data.get('facilities'),
        description=data.get('description')
    )
    db.session.add(branch)
    db.session.commit()
    return jsonify({'message': 'Branch created', 'id': branch.id}), 201

@admin_bp.route('/api/branches/<int:id>', methods=['GET'])
@admin_required
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
            'price': room.price,
            'status': room.status,
            'description': room.description,
            'floor': floor,
            'position_x': room.position_x,
            'position_y': room.position_y,
            'width': room.width,
            'height': room.height
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
        'rooms': [{
            'id': r.id,
            'name': r.name,
            'price': r.price,
            'status': r.status,
            'floor': r.floor
        } for r in branch.rooms],
        'rooms_by_floor': rooms_by_floor,
        'floor_plans': floor_plans
    })

@admin_bp.route('/api/branches/<int:id>', methods=['PUT'])
@admin_required
def update_branch(current_user, id):
    """Update branch"""
    branch = Branch.query.get_or_404(id)
    data = request.get_json()
    
    if 'name' in data:
        branch.name = data['name']
    if 'address' in data:
        branch.address = data['address']
    if 'facilities' in data:
        branch.facilities = data['facilities']
    if 'description' in data:
        branch.description = data['description']
        
    db.session.commit()
    return jsonify({'message': 'Branch updated'})

@admin_bp.route('/api/branches/<int:id>', methods=['DELETE'])
@admin_required
def delete_branch(current_user, id):
    """Delete branch"""
    branch = Branch.query.get_or_404(id)
    if branch.rooms:
        return jsonify({'error': 'Cannot delete branch with rooms'}), 400
    
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
        price=data['price'],
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
    if 'price' in data:
        room.price = data['price']
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
