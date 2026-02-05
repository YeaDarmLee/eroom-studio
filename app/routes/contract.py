from flask import Blueprint, request, jsonify
from app.models.contract import Contract
from app.models.branch import Room
from app.extensions import db
from app.routes.auth import token_required
import datetime

contract_bp = Blueprint('contract', __name__, url_prefix='/api/contracts')

@contract_bp.route('', methods=['POST'])
@token_required
def create_contract(current_user):
    data = request.get_json()
    room_id = data.get('room_id')
    start_date_str = data.get('start_date')
    months = data.get('months', 1)
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    
    room = Room.query.get_or_404(room_id)
    
    try:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'message': 'Invalid date format'}), 400
        
    # Calculate end date
    if room.room_type == 'time_based':
        # For time-based rooms, end_date is the same as start_date
        end_date = start_date
    else:
        # For monthly rooms, calculate based on months
        import calendar
        def add_months(sourcedate, months):
            month = sourcedate.month - 1 + months
            year = sourcedate.year + month // 12
            month = month % 12 + 1
            day = min(sourcedate.day, calendar.monthrange(year,month)[1])
            return datetime.date(year, month, day)
        end_date = add_months(start_date, months)
    
    contract = Contract(
        user_id=current_user.id,
        room_id=room.id,
        start_date=start_date,
        end_date=end_date,
        start_time=start_time,
        end_time=end_time,
        months=months if room.room_type != 'time_based' else 0,
        price=room.price * (data.get('hours', 1) if room.room_type == 'time_based' else 1),
        deposit=room.deposit if room.room_type != 'time_based' else 0,
        status='requested'
    )
    
    db.session.add(contract)
    db.session.commit()
    
    return jsonify({
        'id': contract.id,
        'status': contract.status,
        'price': contract.price,
        'deposit': contract.deposit
    }), 201

@contract_bp.route('', methods=['GET'])
@token_required
def get_my_contracts(current_user):
    contracts = current_user.contracts.all()
    result = []
    for c in contracts:
        result.append({
            'id': c.id,
            'room': {
                'name': c.room.name,
                'branch_name': c.room.branch.name,
                'price': c.room.price,
                'deposit': c.room.deposit,
                'room_type': c.room.room_type
            },
            'start_date': c.start_date.isoformat(),
            'end_date': c.end_date.isoformat(),
            'start_time': c.start_time,
            'end_time': c.end_time,
            'price': c.price,
            'status': c.status
        })
    return jsonify(result)
