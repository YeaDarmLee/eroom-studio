import jwt
import datetime
from flask import current_app
from app.models.user import User
from app.extensions import db

class AuthService:
    @staticmethod
    def generate_token(user_id):
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
            'iat': datetime.datetime.utcnow(),
            'sub': user_id
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
