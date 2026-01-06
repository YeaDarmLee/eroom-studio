import jwt
import datetime
from flask import current_app
from app.models.user import User
from app.extensions import db
from app.services.contract_mapping_service import ContractMappingService

class AuthService:
    @staticmethod
    def generate_token(user_id):
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
            'iat': datetime.datetime.utcnow(),
            'sub': str(user_id)  # JWT 표준에서는 sub가 문자열이어야 함
        }
        return jwt.encode(
            payload,
            current_app.config.get('SECRET_KEY'),
            algorithm='HS256'
        )

    @staticmethod
    def get_or_create_kakao_user(kakao_id, properties):
        user = User.query.filter_by(kakao_id=kakao_id).first()
        if not user:
            role = 'admin' if kakao_id == 'admin_master' else 'user'
            user = User(
                kakao_id=kakao_id,
                name=properties.get('nickname'),
                email=properties.get('email'),
                role=role,
                onboarding_status='not_started'
            )
            db.session.add(user)
            db.session.commit()
            
            # 🔗 새 사용자 생성 시 미매핑 계약 자동 매핑 시도
            mapped_count = ContractMappingService.map_contracts_to_user(user)
            if mapped_count > 0:
                print(f"🎉 {user.name}님에게 {mapped_count}개의 계약이 자동 매핑되었습니다!")
        
        return user

    @staticmethod
    def mock_login(kakao_id='123456789', nickname='Test User'):
        user = AuthService.get_or_create_kakao_user(kakao_id, {'nickname': nickname})
        token = AuthService.generate_token(user.id)
        return {
            'token': token,
            'user': {
                'id': user.id,
                'name': user.name,
                'onboarding_status': user.onboarding_status,
                'role': user.role
            }
        }
