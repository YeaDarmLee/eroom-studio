-- 샘플 이메일 사용자 생성 스크립트
-- 이 스크립트는 테스트용 이메일 계정을 생성합니다.

USE eroom;

-- 먼저 password_hash 컬럼이 있는지 확인하고 없으면 추가
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255) NULL;

-- 샘플 사용자 생성 (Python에서 해시 생성 후 삽입)
-- 아래 명령어를 Python에서 실행하여 해시값을 생성하세요:
-- python create_sample_users.py

-- 또는 API를 통해 생성:
-- curl -X POST http://localhost:5000/api/auth/email-register \
--   -H "Content-Type: application/json" \
--   -d '{"email":"user1@example.com","password":"password123","name":"샘플유저1"}'

/*
===========================================
샘플 계정 정보 (해시화 전 비밀번호)
===========================================

계정 1:
- 이메일: user1@example.com
- 비밀번호: password123
- 이름: 샘플유저1
- 역할: user

계정 2:
- 이메일: user2@example.com
- 비밀번호: password456
- 이름: 샘플유저2
- 역할: user

계정 3:
- 이메일: admin@example.com
- 비밀번호: admin123
- 이름: 샘플관리자
- 역할: admin

===========================================
*/
