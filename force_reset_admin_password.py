"""
관리자 계정 비밀번호를 강제로 재설정하는 스크립트
"""
from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    # admin@example.com 계정 찾기
    admin = User.query.filter_by(email='admin@example.com').first()
    
    if not admin:
        print("❌ admin@example.com 계정을 찾을 수 없습니다.")
    else:
        print(f"✅ 관리자 계정을 찾았습니다: {admin.email}")
        
        # 새 비밀번호 설정
        new_password = 'admin123'
        print(f"비밀번호를 '{new_password}'로 설정합니다...")
        
        admin.set_password(new_password)
        db.session.commit()
        
        print(f"✅ 비밀번호가 성공적으로 변경되었습니다!")
        print(f"\n로그인 정보:")
        print(f"  이메일: {admin.email}")
        print(f"  비밀번호: {new_password}")
        print(f"  역할: {admin.role}")
