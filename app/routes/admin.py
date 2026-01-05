from flask import Blueprint, request, jsonify, current_app, render_template
from app.models import db
from app.models.user import User
from app.models.branch import Branch, Room, BranchFloor, RoomImage, BranchService, BranchImage
from app.models.contract import Contract
from app.models.request import Request
from app.routes.auth import admin_required
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@admin_required
def dashboard(current_user):
    """Admin dashboard page"""
    return render_template('admin/dashboard.html')

@admin_bp.route('/api/stats', methods=['GET'])
@admin_required
def get_stats(current_user):
    """Get dashboard stats"""
    from datetime import datetime, timedelta
    
    total_users = User.query.count()
    active_contracts = Contract.query.filter_by(status='active').count()
    pending_requests = Request.query.filter_by(status='submitted').count()
    
    # Calculate total monthly revenue from active contracts
    active_contracts_list = Contract.query.filter_by(status='active').all()
    total_monthly_revenue = sum(c.room.price for c in active_contracts_list if c.room and c.room.price)
    
    # Calculate total deposit from active contracts
    total_deposit = sum(c.room.deposit or 0 for c in active_contracts_list if c.room)
    
    # Get all room IDs with active contracts
    occupied_room_ids = set(c.room_id for c in active_contracts_list if c.room_id)
    
    # Calculate expiring contracts (ending within 1 month)
    one_month_from_now = (datetime.utcnow() + timedelta(days=30)).date()
    expiring_contracts = [c for c in active_contracts_list if c.end_date and c.end_date <= one_month_from_now]
    expiring_count = len(expiring_contracts)

    
    # Get all branches with their revenue and room status
    branches = Branch.query.all()
    branch_data = []
    
    for branch in branches:
        # Get active contracts for this branch
        branch_contracts = [c for c in active_contracts_list if c.room and c.room.branch_id == branch.id]
        
        # Calculate revenue and deposit for this branch
        branch_monthly_revenue = sum(c.room.price for c in branch_contracts if c.room and c.room.price)
        branch_deposit = sum(c.room.deposit or 0 for c in branch_contracts if c.room)
        
        # Get room status for this branch (based on active contracts)
        branch_room_ids = [r.id for r in branch.rooms]
        total_rooms = len(branch_room_ids)
        occupied_rooms = sum(1 for room_id in branch_room_ids if room_id in occupied_room_ids)
        available_rooms = total_rooms - occupied_rooms
        
        # Calculate expiring contracts for this branch
        branch_expiring = sum(1 for c in branch_contracts if c.end_date and c.end_date <= one_month_from_now)
        
        branch_data.append({
            'id': branch.id,
            'name': branch.name,
            'monthly_revenue': branch_monthly_revenue,
            'deposit': branch_deposit,
            'total_rooms': total_rooms,
            'occupied_rooms': occupied_rooms,
            'available_rooms': available_rooms,
            'expiring_contracts': branch_expiring
        })
    
    # Overall room status (based on active contracts)
    total_rooms = Room.query.count()
    occupied_rooms = len(occupied_room_ids)
    available_rooms = total_rooms - occupied_rooms
    
    return jsonify({
        'stats': {
            'totalUsers': total_users,
            'activeContracts': active_contracts,
            'pendingRequests': pending_requests,
            'expiringContracts': expiring_count,
            'monthlyRevenue': total_monthly_revenue,
            'totalDeposit': total_deposit,
            'totalRooms': total_rooms,
            'occupiedRooms': occupied_rooms,
            'availableRooms': available_rooms
        },
        'branchData': branch_data
    })

@admin_bp.route('/api/contracts', methods=['GET'])
@admin_required
def get_contracts(current_user):
    """Get all contracts with details"""
    contracts = Contract.query.all()
    return jsonify([{
        'id': c.id,
        'user_name': c.user.name if c.user else '알 수 없음',
        'user_email': c.user.email if c.user else '',
        'room_name': c.room.name if c.room else '알 수 없음',
        'branch_name': c.room.branch.name if c.room and c.room.branch else '알 수 없음',
        'deposit': c.room.deposit if c.room else 0,
        'price': c.room.price if c.room else 0,
        'start_date': c.start_date.strftime('%Y-%m-%d'),
        'end_date': c.end_date.strftime('%Y-%m-%d'),
        'status': c.status,
        'created_at': c.created_at.strftime('%Y-%m-%d %H:%M') if c.created_at else ''
    } for c in contracts])

@admin_bp.route('/api/requests', methods=['GET'])
@admin_required
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
        
        results.append({
            'id': r.id,
            'user_name': r.user.name if r.user else '알 수 없음',
            'type': r.type,
            'status': r.status,
            'details': details_data,
            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M'),
            'room_name': r.contract.room.name if r.contract and r.contract.room else (details_data.get('room_name') or 'N/A')
        })
    return jsonify(results)

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
    """Update request status and optionally add admin response"""
    req = Request.query.get_or_404(id)
    data = request.get_json()
    
    if 'status' in data:
        req.status = data['status']
        
        # Add response if provided
        if 'admin_response' in data:
            details_dict = {}
            if req.details:
                try:
                    details_dict = json.loads(req.details)
                except:
                    details_dict = {'raw': req.details}
            
            details_dict['admin_response'] = data['admin_response']
            details_dict['responded_at'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            req.details = json.dumps(details_dict)
            
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
        'facilities': b.facilities,
        'description': b.description,
        'image_url': b.image_url,
        'operating_hours': b.operating_hours,
        'contact': b.contact,
        'traffic_info': b.traffic_info,
        'parking_info': b.parking_info,
        'map_info': b.map_info,
        'images': [{'id': img.id, 'url': img.image_url} for img in b.images],
        'room_count': b.rooms.count(),
        'occupied_count': b.rooms.filter_by(status='occupied').count()
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
            filename = secure_filename(f"branch_{name}_{file.filename}")
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'branches')
            os.makedirs(upload_folder, exist_ok=True)
            
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            
            branch.image_url = f"/static/uploads/branches/{filename}"
    
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
            'price': r.price,
            'deposit': r.deposit,
            'area': r.area,
            'status': r.status,
            'floor': r.floor,
            'images': [{'id': img.id, 'url': img.image_url} for img in r.images]
        } for r in branch.rooms],
        'rooms_by_floor': rooms_by_floor,
        'floor_plans': floor_plans,
        'floors': [f.floor for f in branch.floors],
        'image_url': branch.image_url,
        'images': [{'id': img.id, 'url': img.image_url} for img in branch.images],
        'common_services': [{
            'id': s.id,
            'name': s.name,
            'description': s.description,
            'icon': s.icon,
            'service_type': s.service_type
        } for s in branch.services.filter_by(service_type='common').all()],
        'specialized_services': [{
            'id': s.id,
            'name': s.name,
            'description': s.description,
            'icon': s.icon,
            'service_type': s.service_type
        } for s in branch.services.filter_by(service_type='specialized').all()]
    })

@admin_bp.route('/api/branches/<int:branch_id>/services', methods=['POST'])
@admin_required
def create_branch_service(current_user, branch_id):
    """Create branch service"""
    data = request.get_json()
    service = BranchService(
        branch_id=branch_id,
        service_type=data.get('service_type', 'common'),
        name=data['name'],
        description=data.get('description'),
        icon=data.get('icon')
    )
    db.session.add(service)
    db.session.commit()
    return jsonify({'message': 'Service created', 'id': service.id}), 201

@admin_bp.route('/api/branches/<int:branch_id>/services/<int:service_id>', methods=['PUT', 'DELETE'])
@admin_required
def manage_branch_service(current_user, branch_id, service_id):
    """Update or delete branch service"""
    service = BranchService.query.filter_by(id=service_id, branch_id=branch_id).first_or_404()
    
    if request.method == 'DELETE':
        db.session.delete(service)
        db.session.commit()
        return jsonify({'message': 'Service deleted'})
    
    data = request.get_json()
    if 'name' in data:
        service.name = data['name']
    if 'description' in data:
        service.description = data['description']
    if 'icon' in data:
        service.icon = data['icon']
    if 'service_type' in data:
        service.service_type = data['service_type']
        
    db.session.commit()
    return jsonify({'message': 'Service updated'})

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
                filename = secure_filename(f"branch_{branch.name}_{file.filename}")
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'branches')
                os.makedirs(upload_folder, exist_ok=True)
                
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                
                branch.image_url = f"/static/uploads/branches/{filename}"
    
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
