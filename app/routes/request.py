from flask import Blueprint, request, jsonify
from app.models.request import Request
from app.models.contract import Contract
from app.extensions import db
from app.routes.auth import token_required
from app.utils.evidence import log_contract_status_change, get_termination_text_template
from datetime import datetime
from dateutil.relativedelta import relativedelta
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
            
    # --- Termination Defense (New) ---
    if req_type == 'termination' and contract:
        contract.termination_requested_at = datetime.utcnow()
        contract.termination_confirmation_checked = data.get('termination_confirmation_checked', False)
        
        # Calculate Remaining Months & Penalty (Simplified Logic for Snapshot)
        today = datetime.utcnow().date()
        if contract.end_date > today:
            diff = relativedelta(contract.end_date, today)
            contract.remaining_months_at_termination = diff.years * 12 + diff.months
        else:
            contract.remaining_months_at_termination = 0
            
        # Example Penalty: 1 month rent if remaining > 0 (This should match the UI logic)
        penalty_amount = contract.price if contract.remaining_months_at_termination > 0 else 0
        contract.penalty_amount_snapshot = {
            'remaining_months': contract.remaining_months_at_termination,
            'penalty_amount': penalty_amount,
            'calculated_at': datetime.utcnow().isoformat()
        }
        
        # Server-rendered confirmation text
        contract.termination_confirmation_text_snapshot = get_termination_text_template(
            contract, 
            contract.remaining_months_at_termination,
            penalty_amount
        )
        
        # Update Contract Status to 'terminate_requested'
        old_status = contract.status
        contract.status = 'terminate_requested'
        # Save termination date if provided
        termination_date_str = details.get('termination_date')
        if termination_date_str:
            try:
                contract.termination_effective_date = datetime.strptime(termination_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        log_contract_status_change(
            contract=contract,
            old_status=old_status,
            new_status='terminate_requested',
            actor_id=current_user.id,
            actor_type='user',
            source='public_api',
            reason='User requested termination'
        )

    new_request = Request(
        user_id=current_user.id,
        contract_id=contract_id,
        type=req_type,
        details=json.dumps(details),
        status='submitted'
    )
    
    db.session.add(new_request)
    db.session.commit()
    
    # --- SMS Trigger (New) ---
    if req_type == 'termination' and contract:
        try:
            from app.utils.sms_service import sms_service
            from app.utils.sms_context import build_sms_context
            
            # Use the requested termination date for the message if available
            m_date = details.get('termination_date')
            context = build_sms_context(contract, 'MOVEOUT_APPLIED', moveout_date=m_date)
            
            sms_service.send_sms(contract.id, 'MOVEOUT_APPLIED', context)
        except Exception as e:
            print(f"SMS trigger error (MOVEOUT_APPLIED): {e}")

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
