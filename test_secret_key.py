"""
SECRET_KEY 확인 및 토큰 생성/검증 테스트
"""
from app import create_app
from app.services.auth_service import AuthService
import jwt

app = create_app()

with app.app_context():
    secret_key = app.config.get('SECRET_KEY')
    print(f"현재 SECRET_KEY: {secret_key}")
    print(f"SECRET_KEY 길이: {len(secret_key) if secret_key else 0}")
    print()
    
    # 테스트 토큰 생성
    test_user_id = 2  # admin 계정 ID
    print(f"테스트: User ID {test_user_id}로 토큰 생성...")
    token = AuthService.generate_token(test_user_id)
    print(f"생성된 토큰: {token[:50]}...")
    print()
    
    # 토큰 검증
    try:
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
        print(f"✅ 토큰 검증 성공!")
        print(f"Decoded payload: {decoded}")
    except Exception as e:
        print(f"❌ 토큰 검증 실패: {str(e)}")
