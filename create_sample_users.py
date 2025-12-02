"""
샘플 이메일 사용자 생성 스크립트

이 스크립트는 테스트용 이메일 계정을 MySQL 데이터베이스에 직접 생성합니다.
비밀번호는 werkzeug.security를 사용하여 해시화됩니다.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.user import User

def create_sample_users():
    """샘플 사용자 생성"""
    app = create_app()
    
    with app.app_context():
        # 샘플 계정 정보
        sample_users = [
            {
                'email': 'user1@example.com',
                'password': 'password123',
                'name': '샘플유저1',
                'role': 'user'
            },
            {
                'email': 'user2@example.com',
                'password': 'password456',
                'name': '샘플유저2',
                'role': 'user'
            },
            {
                'email': 'admin@example.com',
                'password': 'admin123',
                'name': '샘플관리자',
                'role': 'admin'
            }
        ]
        
        print("=" * 60)
        print("샘플 사용자 생성 중...")
        print("=" * 60)
        
        for user_data in sample_users:
            # 이미 존재하는지 확인
            existing_user = User.query.filter_by(email=user_data['email']).first()
            
            if existing_user:
                print(f"⚠️  {user_data['email']} - 이미 존재합니다. 건너뜁니다.")
                continue
            
            # 새 사용자 생성
            user = User(
                email=user_data['email'],
                name=user_data['name'],
                role=user_data['role'],
                onboarding_status='new_user_done'
            )
            user.set_password(user_data['password'])
            
            db.session.add(user)
            print(f"✅ {user_data['email']} - 생성 완료")
        
        db.session.commit()
        
        print("=" * 60)
        print("샘플 사용자 생성 완료!")
        print("=" * 60)
        print("\n로그인 정보:")
        print("-" * 60)
        for user_data in sample_users:
            print(f"이메일: {user_data['email']}")
            print(f"비밀번호: {user_data['password']}")
            print(f"이름: {user_data['name']}")
            print(f"역할: {user_data['role']}")
            print("-" * 60)

if __name__ == '__main__':
    create_sample_users()
