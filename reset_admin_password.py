"""
관리자 비밀번호 재설정 스크립트
scrypt -> pbkdf2:sha256 마이그레이션을 위해 관리자 비밀번호를 재설정합니다.
"""
from app import create_app, db
from app.models.user import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # 모든 관리자 계정 찾기
    admin_users = User.query.filter_by(role='admin').all()
    
    if not admin_users:
        print("❌ 관리자 계정을 찾을 수 없습니다.")
    else:
        print(f"✅ {len(admin_users)}개의 관리자 계정을 찾았습니다.\n")
        
        for admin in admin_users:
            print(f"관리자: {admin.email or admin.name or f'ID: {admin.id}'}")
            
            # 비밀번호를 'admin123'으로 재설정 (또는 원하는 비밀번호로 변경)
            new_password = 'admin123'
            admin.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
            
            print(f"  → 비밀번호가 '{new_password}'로 재설정되었습니다.")
        
        db.session.commit()
        print("\n✅ 모든 관리자 계정의 비밀번호가 성공적으로 재설정되었습니다.")
        print("⚠️  보안을 위해 로그인 후 비밀번호를 변경하세요!")
