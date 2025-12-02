from flask import Blueprint, request, jsonify
from app.models.request import Request
from app.models.contract import Contract
from app.extensions import db
from app.routes.auth import token_required
import json

request_bp = Blueprint('request', __name__, url_prefix='/api/requests')

@request_bp.route('', methods=['POST'])
@token_required
def create_request(current_user):
    data = request.get_json()
    req_type = data.get('type')
    contract_id = data.get('contract_id')
    details = data.get('details', {})
    
    if contract_id:
        contract = Contract.query.get(contract_id)
        if not contract or contract.user_id != current_user.id:
            return jsonify({'message': 'Invalid contract'}), 400
            
    new_request = Request(
        user_id=current_user.id,
        contract_id=contract_id,
        type=req_type,
        details=json.dumps(details),
        status='submitted'
    )
    
    db.session.add(new_request)
    db.session.commit()
    
    return jsonify({'id': new_request.id, 'status': new_request.status}), 201

@request_bp.route('', methods=['GET'])
@token_required
def get_my_requests(current_user):
    requests = current_user.requests.order_by(Request.created_at.desc()).all()
    result = []
    for r in requests:
        result.append({
            'id': r.id,
            'type': r.type,
            'status': r.status,
            'created_at': r.created_at.isoformat(),
            'details': json.loads(r.details) if r.details else {}
        })
    return jsonify(result)
