from flask import Blueprint, request, jsonify
from app.models.request import Request
from app.models.contract import Contract
from app.extensions import db
from app.routes.auth import token_required
from app.utils.evidence import log_contract_status_change, get_termination_text_template
from datetime import datetime
import json

request_bp = Blueprint('request', __name__, url_prefix='/api/requests')

@request_bp.route('', methods=['POST'])
@token_required
def create_request(current_user):
    data = request.get_json()
    req_type = data.get('type')
    contract_id = data.get('contract_id')
    details = data.get('details', {})
    if req_type not in ('repair', 'supplies', 'extension', 'termination', 'inquiry', 'complaint', 'other') or not isinstance(details, dict):
        return jsonify({'message': '올바른 요청 유형과 내용을 입력해주세요.'}), 400
    contract = None
    
    if contract_id:
        contract = Contract.query.get(contract_id)
        if not contract or contract.user_id != current_user.id:
            return jsonify({'message': 'Invalid contract'}), 400
            
    if req_type == 'termination':
        if not contract:
            return jsonify({'message': '계약을 선택해주세요.'}), 400
        try:
            termination_date = datetime.strptime(details.get('termination_date'), '%Y-%m-%d').date()
        except (TypeError, ValueError):
            return jsonify({'message': '퇴실일을 YYYY-MM-DD 형식으로 입력해주세요.'}), 400
        if termination_date < contract.start_date:
            return jsonify({'message': '퇴실일은 계약 시작일 이후여야 합니다.'}), 400
        if contract.status != 'active' or contract.auto_extend_status == 'will_terminate':
            return jsonify({'message': '현재 계약 상태에서는 퇴실을 다시 신청할 수 없습니다.'}), 409

    if req_type == 'extension':
        from app.services.contract_rules import positive_int
        if not contract or contract.status != 'active' or contract.auto_extend_status == 'will_terminate':
            return jsonify({'message': '연장 가능한 계약을 선택해주세요.'}), 400
        details['extension_months'] = positive_int(details.get('extension_months'), '연장 개월 수', 36)

    if req_type == 'inquiry' and details.get('room_id'):
        from app.models.branch import Room
        room = Room.query.get_or_404(details['room_id'])
        details.update(room_id=room.id, room_name=room.name, branch_id=room.branch_id)

    # --- Termination Defense (New) ---
    if req_type == 'termination' and contract:
        old_status = contract.status
        termination_date_str = details.get('termination_date')
        
        # Use single-transaction domain method
        contract.apply_termination_request(
            termination_date=termination_date_str,
            confirmation_checked=data.get('termination_confirmation_checked', False)
        )

        contract.termination_confirmation_text_snapshot = get_termination_text_template(
            contract,
            contract.remaining_months_at_termination,
            contract.penalty_amount_snapshot['penalty_amount']
        )

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
    try:
        from app.utils.sms_service import sms_service
        from app.utils.sms_context import build_sms_context

        if req_type == 'termination' and contract:
            # Use the requested termination date for the message if available
            m_date = details.get('termination_date')
            context = build_sms_context(contract, 'MOVEOUT_APPLIED', moveout_date=m_date)
            sms_service.send_sms(contract.id, 'MOVEOUT_APPLIED', context)
            
        elif req_type == 'extension' and contract:
            # Notify ADMIN about extension request
            admin_phone = contract.room.branch.owner_contact if contract.room and contract.room.branch else None
            if admin_phone:
                extend_months = details.get('extension_months', '?')
                context = build_sms_context(contract, 'EXTEND_APPLIED', extend_months=extend_months)
                sms_service.send_sms(contract.id, 'EXTEND_APPLIED', context, to_number=admin_phone)

    except Exception as e:
        print(f"SMS trigger error in request creation: {e}")

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
