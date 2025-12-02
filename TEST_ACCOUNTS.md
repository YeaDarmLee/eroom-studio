# 테스트 계정 관리 가이드

## 📌 개요

Eroom-Studio는 개발 및 테스트를 위해 **두 개의 고정 테스트 계정**을 사용합니다.
이 계정들은 MySQL `users` 테이블의 **id=1 (일반 사용자)** 및 **id=2 (관리자)** 레코드입니다.

## 🔑 테스트 계정 정보

### 1. 일반 사용자 계정 (id=1)

| 항목 | 값 |
|------|-----|
| **User ID** | 1 |
| **Role** | `user` |
| **로그인 방법** | `/login` → "Login with Kakao (Mock)" |
| **API 엔드포인트** | `POST /api/auth/mock-login` |
| **용도** | 사용자 기능 테스트 (대시보드, 계약 신청, 요청 제출) |

### 2. 관리자 계정 (id=2)

| 항목 | 값 |
|------|-----|
| **User ID** | 2 |
| **Role** | `admin` |
| **로그인 방법** | `/login` → "관리자 로그인 (DEV)" |
| **API 엔드포인트** | `POST /api/auth/mock-admin-login` |
| **용도** | 관리자 기능 테스트 (계약/요청 관리, 통계 확인) |

## 🔒 Mock 로그인 동작 방식

### 현재 구현된 로직

```python
# POST /api/auth/mock-login
user = User.query.get(1)
if not user:
    # 계정이 없을 때만 생성
    user = User(id=1, kakao_id='...', email='...', ...)
    db.session.add(user)
    db.session.commit()

# 계정이 이미 존재하면 DB 값을 그대로 사용
access_token = generate_token(user.id)
return jsonify({...})
```

### 핵심 원칙

> [!IMPORTANT]
> **"DB가 소스 오브 트루스(Source of Truth)"**
> 
> - ✅ **계정이 존재하면**: DB의 값을 **절대 변경하지 않음**
> - ✅ **계정이 없으면**: 기본값으로 **한 번만 생성**
> - ✅ **덮어쓰기 없음**: `email`, `name`, `role`, `onboarding_status` 등 모든 필드 보존

## 🛠️ 테스트 계정 커스터마이징

### 방법 1: MySQL에서 직접 수정

```sql
USE eroom;

-- 일반 사용자 계정 수정
UPDATE users
SET
  kakao_id = 'your_real_kakao_id',
  email = 'your_email@example.com',
  name = '본인 이름',
  role = 'user',
  onboarding_status = 'existing_linked'
WHERE id = 1;

-- 관리자 계정 수정
UPDATE users
SET
  kakao_id = 'admin_kakao_id',
  email = 'admin@example.com',
  name = '관리자 이름',
  role = 'admin',
  onboarding_status = 'new_user_done'
WHERE id = 2;

-- 변경 확인
SELECT id, kakao_id, email, name, role, onboarding_status FROM users WHERE id IN (1, 2);
```

### 방법 2: SQL 스크립트 작성

테스트 계정 설정을 스크립트로 관리하면 DB 초기화 시 편리합니다:

```sql
-- seed_test_accounts.sql
USE eroom;

-- 기존 계정 삭제 (선택사항)
DELETE FROM users WHERE id IN (1, 2);

-- 테스트 계정 생성
INSERT INTO users (id, kakao_id, email, name, role, onboarding_status, created_at)
VALUES
  (1, 'kakao_test_user', 'user@test.com', '테스트유저', 'user', 'existing_linked', NOW()),
  (2, 'kakao_admin', 'admin@test.com', '관리자', 'admin', 'new_user_done', NOW())
ON DUPLICATE KEY UPDATE
  kakao_id = VALUES(kakao_id),
  email = VALUES(email),
  name = VALUES(name),
  role = VALUES(role),
  onboarding_status = VALUES(onboarding_status);
```

실행:
```bash
mysql -u root -p eroom < seed_test_accounts.sql
```

## 🔄 DB 초기화 시 복원 절차

### 시나리오: DB를 완전히 초기화한 경우

1. **마이그레이션 실행**
   ```bash
   flask db upgrade
   ```

2. **테스트 계정 복원**
   ```sql
   USE eroom;
   
   -- 본인의 테스트 계정 정보로 수정
   INSERT INTO users (id, kakao_id, email, name, role, onboarding_status, created_at)
   VALUES
     (1, 'your_kakao_id', 'your_email@example.com', '본인 이름', 'user', 'existing_linked', NOW()),
     (2, 'admin_kakao_id', 'admin@example.com', '관리자 이름', 'admin', 'new_user_done', NOW());
   ```

3. **로그인 테스트**
   - `/login` → "Login with Kakao (Mock)" → 본인 계정으로 로그인 확인
   - `/login` → "관리자 로그인 (DEV)" → 관리자 계정으로 로그인 확인

## 📝 베스트 프랙티스

### 1. 테스트 계정 정보 백업

테스트 계정 정보를 별도 파일로 저장해두면 편리합니다:

```sql
-- my_test_accounts.sql
-- 본인의 테스트 계정 정보 (Git에 커밋하지 말 것!)
USE eroom;

UPDATE users SET
  kakao_id = 'my_real_kakao_id',
  email = 'my_email@example.com',
  name = '내 이름',
  role = 'user',
  onboarding_status = 'existing_linked'
WHERE id = 1;

UPDATE users SET
  kakao_id = 'my_admin_kakao_id',
  email = 'my_admin@example.com',
  name = '관리자',
  role = 'admin',
  onboarding_status = 'new_user_done'
WHERE id = 2;
```

### 2. .gitignore에 추가

```
# .gitignore
my_test_accounts.sql
*_test_accounts.sql
```

### 3. 팀 공유 시

팀원들과 공유할 때는 템플릿만 제공:

```sql
-- test_accounts.template.sql
USE eroom;

UPDATE users SET
  kakao_id = 'YOUR_KAKAO_ID_HERE',
  email = 'YOUR_EMAIL_HERE',
  name = 'YOUR_NAME_HERE',
  role = 'user',
  onboarding_status = 'existing_linked'
WHERE id = 1;

-- ... (id=2도 동일)
```

## 🧪 테스트 시나리오

### 일반 사용자 플로우
1. `/login` → "Login with Kakao (Mock)"
2. `/my/room` → 계약 정보 확인
3. 요청 제출 (수리, 비품 등)
4. 요청 상태 확인

### 관리자 플로우
1. `/login` → "관리자 로그인 (DEV)"
2. `/admin` → 대시보드 확인
3. 계약 승인/거절
4. 요청 처리 (처리중/완료)

## ⚠️ 주의사항

1. **절대 프로덕션에서 사용 금지**
   - Mock 로그인은 개발/테스트 전용입니다.
   - 프로덕션에서는 실제 Kakao OAuth를 구현해야 합니다.

2. **id=1, id=2는 예약됨**
   - 이 두 ID는 테스트 계정 전용입니다.
   - 실제 사용자는 id=3부터 시작하도록 합니다.

3. **비밀번호 없음**
   - Mock 로그인은 인증 없이 바로 토큰을 발급합니다.
   - 보안이 필요한 환경에서는 사용하지 마세요.

## 🔍 트러블슈팅

### Q: Mock 로그인 후 내 정보가 아닌 기본값이 나옵니다.

**A**: DB에 계정이 없어서 자동 생성된 것입니다. 위의 "테스트 계정 커스터마이징" 절차를 따라 수정하세요.

### Q: 계정을 수정했는데 여전히 이전 정보가 나옵니다.

**A**: 
1. 브라우저 localStorage를 클리어하세요 (F12 → Application → Local Storage → Clear)
2. 다시 로그인하세요.

### Q: DB를 초기화했더니 테스트 계정이 사라졌습니다.

**A**: 위의 "DB 초기화 시 복원 절차"를 따라 계정을 다시 생성하세요.

---

**마지막 업데이트**: 2025-11-30  
**관련 문서**: 
- [USER_GUIDE.md](file:///c:/workspace/Eroom-Studio/USER_GUIDE.md)
- [walkthrough.md](file:///C:/Users/gnswp/.gemini/antigravity/brain/a8a73801-b24f-48c7-8274-4fa3ea057e90/walkthrough.md)
