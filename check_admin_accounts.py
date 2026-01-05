"""
관리자 계정 정보 조회 스크립트
"""
from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    # 모든 관리자 계정 찾기
    admin_users = User.query.filter_by(role='admin').all()
    
    if not admin_users:
        print("❌ 관리자 계정을 찾을 수 없습니다.")
        
        # 모든 사용자 확인
        all_users = User.query.all()
        print(f"\n전체 사용자 수: {len(all_users)}")
        for user in all_users:
            print(f"  - ID: {user.id}, Email: {user.email}, Name: {user.name}, Role: {user.role}")
    else:
        print(f"✅ {len(admin_users)}개의 관리자 계정을 찾았습니다.\n")
        
        for admin in admin_users:
            print(f"관리자 계정:")
            print(f"  - ID: {admin.id}")
            print(f"  - 이메일: {admin.email}")
            print(f"  - 이름: {admin.name}")
            print(f"  - 역할: {admin.role}")
            print(f"  - 비밀번호 해시 존재: {'예' if admin.password_hash else '아니오'}")
            print()
