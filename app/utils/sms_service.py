import re
import json
import logging
import requests
from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models.sms import SmsTemplate, SmsLog, get_kst_now

logger = logging.getLogger(__name__)

# --- Source of Truth: 타입별 허용 변수 목록 ---
SMS_VARIABLE_SCHEMA = {
    'CONTRACT_APPLIED': ['user_name', 'branch_name', 'room_name'],
    'CONTRACT_APPROVED': ['user_name', 'branch_name', 'room_name', 'start_date', 'due_date'],
    'PAYMENT_REMINDER': ['user_name', 'branch_name', 'room_name', 'due_date', 'amount'],
    'AUTO_RENEW_NOTICE': ['user_name', 'branch_name', 'room_name', 'end_date', 'renew_deadline'],
    'MOVEOUT_APPLIED': ['user_name', 'branch_name', 'room_name', 'moveout_date'],
    'MOVEOUT_APPROVED': ['user_name', 'branch_name', 'room_name', 'moveout_date', 'deposit_refund_date'],
    'MOVEOUT_DAY': ['user_name', 'branch_name', 'room_name'],
    'PAYMENT_OVERDUE_STAGE1': ['user_name', 'branch_name', 'amount', 'due_date'],
    'PAYMENT_OVERDUE_STAGE2': ['user_name', 'branch_name', 'amount', 'due_date']
}

class SmsProviderInterface:
    def send(self, to_number, content):
        raise NotImplementedError

class SmsProviderStub(SmsProviderInterface):
    """실제 발송은 하지 않고 로그만 남기는 Stub"""
    def send(self, to_number, content):
        logger.info(f"[SMS STUB] To: {to_number} | Content: {content}")
        return f"stub_msg_{datetime.now().timestamp()}"

class AligoSmsProvider(SmsProviderInterface):
    """알리고 문자를 통한 실제 발송"""
    def __init__(self, api_key, user_id, sender):
        self.api_key = api_key
        self.user_id = user_id
        self.sender = sender
        self.api_url = "https://apis.aligo.in/send/"

    def send(self, to_number, content):
        # 알리고 API 규격에 맞춘 데이터 구성
        data = {
            'key': self.api_key,
            'user_id': self.user_id,
            'sender': self.sender,
            'receiver': to_number,
            'msg': content,
            # 'testmode_yn': 'Y' # 필요시 테스트 모드 활성화
        }
        
        try:
            response = requests.post(self.api_url, data=data)
            res_json = response.json()
            
            # 알리고 응답 코드 확인: result_code가 1이면 성공
            if res_json.get('result_code') == '1':
                return str(res_json.get('msg_id'))
            else:
                # 실패 시 예외 발생시켜 로깅되도록 함
                error_msg = res_json.get('message', 'Unknown Error')
                raise Exception(f"Aligo API Error: {res_json.get('result_code')} - {error_msg}")
                
        except Exception as e:
            logger.error(f"Aligo SMS Send Failed: {str(e)}")
            raise e

class SmsService:
    def __init__(self):
        pass

    def _get_provider(self):
        """현재 앱 컨텍스트 설정에 따라 Provider 반환"""
        api_key = current_app.config.get('ALIGO_API_KEY')
        user_id = current_app.config.get('ALIGO_USER_ID')
        sender = current_app.config.get('ALIGO_SENDER')

        if api_key and user_id and sender:
            return AligoSmsProvider(api_key, user_id, sender), "Aligo"
        return SmsProviderStub(), "Stub"

    def get_template(self, msg_type):
        """SMS 템플릿 조회"""
        return SmsTemplate.query.filter_by(type=msg_type, is_active=True).first()

    def render_template(self, template_str, context):
        """
        {{variable}} 형태의 변수를 context 데이터로 치환합니다.
        치환되지 않은 변수가 남아있으면 (text, list_of_missing_vars)를 반환합니다.
        """
        missing_vars = []
        rendered = template_str
        
        # 중복된 변수들 추출
        placeholders = re.findall(r'\{\{(.*?)\}\}', template_str)
        
        for p in placeholders:
            val = context.get(p.strip())
            if val is not None:
                rendered = rendered.replace(f'{{{{{p}}}}}', str(val))
            else:
                missing_vars.append(p)
        
        return rendered, missing_vars

    def send_sms(self, contract_id, msg_type, context, related_date=None, to_number=None, content_override=None, force_send=False):
        """
        문자 발송 통합 함수 (Idempotency & Validation 포함)
        """
        # 1. 템플릿 조회
        content_template = ""
        if content_override:
            content_template = content_override
        else:
            template = SmsTemplate.query.filter_by(type=msg_type, is_active=True).first()
            if not template:
                logger.error(f"SMS Template not found or inactive: {msg_type}")
                return False, "Template not found"
            content_template = template.content

        # 2. dedup_key 생성 (Decision 1: {type}:{contract_id}:{related_date})
        r_date = related_date or get_kst_now().date()
        dedup_key = f"{msg_type}:{contract_id}:{r_date}"
        
        if force_send:
            # 수동 발송 등 강제 전송 시 유니크 키 생성 (Timestamp 추가)
            dedup_key += f":force:{int(datetime.now().timestamp())}"

        # 3. 중복 체크 (Decision 3: UNIQUE(dedup_key))
        existing_log = SmsLog.query.filter_by(dedup_key=dedup_key).first()
        if existing_log:
            logger.info(f"SMS Skipped (Duplicate): {dedup_key}")
            return True, "Skipped(Duplicate)"

        # 4. 수신 번호 확인 (Context에 있는 경우 우선)
        target_number = to_number or context.get('user_phone')
        if not target_number:
            return False, "Receiver phone number missing"

        # 5. 렌더링 및 검증 (Decision 5 & 6)
        logger.info(f"[SMS Debug] Sending {msg_type} to {target_number}. Context keys: {list(context.keys())}")
        content, missing = self.render_template(content_template, context)
        
        if missing:
            # 렌더링 실패 로그 기록 (Decision 6: FAILED)
            self._create_log(
                contract_id=contract_id,
                msg_type=msg_type,
                dedup_key=dedup_key,
                related_date=r_date,
                content=content,
                context=context,
                status="FAILED",
                error_message=f"Missing variables: {', '.join(missing)}"
            )
            return False, f"Missing variables: {missing}"

        # 6. 실제 발송
        provider, provider_name = self._get_provider()
        try:
            provider_msg_id = provider.send(target_number, content)
            
            # 발송 성공 로그 (Decision 6: SENT(Provider))
            self._create_log(
                contract_id=contract_id,
                msg_type=msg_type,
                dedup_key=dedup_key,
                related_date=r_date,
                content=content,
                context=context,
                status=f"SENT({provider_name})",
                provider_info=provider_name,
                provider_message_id=provider_msg_id
            )
            return True, "Sent"
        except Exception as e:
            logger.exception("SMS provider error")
            self._create_log(
                contract_id=contract_id,
                msg_type=msg_type,
                dedup_key=dedup_key,
                related_date=r_date,
                content=content,
                context=context,
                status="FAILED",
                error_message=str(e)
            )
            return False, str(e)

    def _create_log(self, **kwargs):
        """로그 생성 Helper"""
        new_log = SmsLog(
            contract_id=kwargs.get('contract_id'),
            type=kwargs.get('msg_type'),
            dedup_key=kwargs.get('dedup_key'),
            related_date=kwargs.get('related_date'),
            content_snapshot=kwargs.get('content'),
            context_snapshot=kwargs.get('context'),
            status=kwargs.get('status'),
            provider_info=kwargs.get('provider_info'),
            provider_message_id=kwargs.get('provider_message_id'),
            error_message=kwargs.get('error_message')
        )
        db.session.add(new_log)
        db.session.commit()
        return new_log

# 싱글톤 인스턴스 (Decision 4와 연계 - 앱 내에서 공유)
sms_service = SmsService()
