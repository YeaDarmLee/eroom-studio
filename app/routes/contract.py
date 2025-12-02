from flask import Blueprint, request, jsonify
from app.models.contract import Contract
from app.models.branch import Room
from app.extensions import db
from app.routes.auth import token_required
from datetime import datetime

contract_bp = Blueprint('contract', __name__, url_prefix='/api/contracts')

@contract_bp.route('', methods=['POST'])
@token_required
def create_contract(current_user):
    data = request.get_json()
    room_id = data.get('room_id')
    start_date_str = data.get('start_date')
    months = data.get('months', 1)
    
    room = Room.query.get_or_404(room_id)
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'message': 'Invalid date format'}), 400
        
    # Calculate end date (simple logic for now)
    # In real app, consider month length
    import calendar
    def add_months(sourcedate, months):
        month = sourcedate.month - 1 + months
        year = sourcedate.year + month // 12
        month = month % 12 + 1
        day = min(sourcedate.day, calendar.monthrange(year,month)[1])
        return datetime.date(year, month, day)

    end_date = add_months(start_date, months)
    total_price = room.price * months
    
    contract = Contract(
        user_id=current_user.id,
        room_id=room.id,
        start_date=start_date,
        end_date=end_date,
        months=months,
        total_price=total_price,
        status='requested'
    )
    
    db.session.add(contract)
    db.session.commit()
    
    return jsonify({
        'id': contract.id,
        'status': contract.status,
        'total_price': contract.total_price
    }), 201

@contract_bp.route('', methods=['GET'])
@token_required
def get_my_contracts(current_user):
    contracts = current_user.contracts.all()
    result = []
    for c in contracts:
        result.append({
            'id': c.id,
            'room_name': c.room.name,
            'branch_name': c.room.branch.name,
            'start_date': c.start_date.isoformat(),
            'end_date': c.end_date.isoformat(),
            'status': c.status
        })
    return jsonify(result)
