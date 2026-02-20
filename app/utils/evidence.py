import hashlib
import json
import os
from datetime import datetime
from flask import request, current_app
from app.extensions import db
from app.models.contract import ContractStatusHistory, TermsDocument

def log_contract_status_change(contract, old_status, new_status, actor_id=None, actor_type='system', reason=None, source='system'):
    """로그 기록: 누가, 언제, 어디서 상태를 변경했는지 기록합니다."""
    # Get IP and User-Agent if in request context
    actor_ip = None
    actor_user_agent = None
    if request:
        actor_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        actor_user_agent = request.headers.get('User-Agent')
        if not actor_id and 'admin' in request.path:
            # Simple assumption if actor_id not passed but in admin path
            pass 

    history = ContractStatusHistory(
        contract_id=contract.id,
        old_status=old_status,
        new_status=new_status,
        actor_id=actor_id,
        actor_type=actor_type,
        actor_ip=actor_ip,
        actor_user_agent=actor_user_agent,
        source=source,
        reason=reason
    )
    db.session.add(history)
    return history

def get_server_side_terms(version):
    """서버에 저장된 특정 버전의 약관 정보를 가져옵니다."""
    return TermsDocument.query.filter_by(version=version, is_active=True).first()

def generate_content_hash(content):
    """내용의 SHA256 해시를 생성합니다."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def ensure_private_dir(contract_id):
    """비공개 저장 경로가 존재하는지 확인하고 경로를 반환합니다."""
    base_dir = os.path.join(current_app.root_path, 'private', 'contracts', str(contract_id))
    os.makedirs(base_dir, exist_ok=True)
    return base_dir

def get_termination_text_template(contract, remaining_months, penalty_amount):
    """해지 시 사용자에게 보여줄 안내 문구 템플릿을 생성합니다 (서버 렌더링)."""
    return f"""[중도해지 확인서]
계약 번호: {contract.id}
해지 요청일: {datetime.now().strftime('%Y-%m-%d')}
잔여 기간: {remaining_months}개월
예상 위약금: {format(penalty_amount, ',')}원

본인은 위 위약금 발생 사실을 충분히 인지하였으며, 
이룸 스튜디오의 중도해지 정책에 따라 해지를 진행함에 동의합니다."""
