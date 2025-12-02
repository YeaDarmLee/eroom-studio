# 이룸 스튜디오 웹 관리 시스템 - 사용 및 설정 가이드

이 문서는 이룸 스튜디오(Eroom Studio) 웹 관리 시스템의 설치, 설정 및 사용 방법을 설명합니다.

---

## 🔑 테스트 계정 안내

### 기본 테스트 계정

시스템은 **두 개의 고정 테스트 계정**을 사용합니다 (MySQL `users` 테이블의 id=1, id=2):

**1. 일반 사용자 (id=1)**
- **역할**: `user`
- **로그인 방법**: `/login` 페이지에서 "Login with Kakao (Mock)" 클릭
- **용도**: 사용자 기능 테스트 (대시보드, 계약, 요청)

**2. 관리자 (id=2)**
- **역할**: `admin`
- **로그인 방법**: `/login` 페이지에서 "관리자 로그인 (DEV)" 클릭
- **용도**: 관리자 기능 테스트 (대시보드, 계약/요청 관리)

### 중요 사항

*   **DB 기반**: Mock 로그인은 데이터베이스의 `users` 테이블에서 id=1, id=2 계정을 읽어옵니다.
*   **데이터 보존**: 계정이 이미 존재하면 **절대 덮어쓰지 않습니다**. DB의 값을 그대로 사용합니다.
*   **자동 생성**: 계정이 존재하지 않을 때만 기본값으로 자동 생성됩니다.
*   **커스터마이징 가능**: MySQL에서 직접 계정 정보를 수정하여 본인의 테스트 데이터를 사용할 수 있습니다.

### 테스트 계정 커스터마이징

MySQL에서 직접 계정 정보를 수정할 수 있습니다:

```sql
USE eroom;

-- 일반 사용자 계정 수정 (id=1)
UPDATE users
SET
  kakao_id = 'your_kakao_id',
  email = 'your_email@example.com',
  name = '본인 이름',
  role = 'user',
  onboarding_status = 'existing_linked'
WHERE id = 1;

-- 관리자 계정 수정 (id=2)
UPDATE users
SET
  kakao_id = 'admin_kakao_id',
  email = 'admin@example.com',
  name = '관리자 이름',
  role = 'admin',
  onboarding_status = 'new_user_done'
WHERE id = 2;
```

수정 후, Mock 로그인 시 커스터마이징한 데이터가 그대로 사용됩니다.

---

## 1. 환경 설정 (Setup)

### 필수 요구 사항
*   **Python 3.9** 이상
*   **Git**
*   (선택 사항) **Docker** & **Docker Compose**

### 설치 단계 (로컬 실행)

1.  **프로젝트 클론**
    ```bash
    git clone <repository-url>
    cd Eroom-Studio
    ```

2.  **가상 환경 생성 및 활성화** (권장)
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **의존성 패키지 설치**
    ```bash
    pip install -r requirements.txt
    ```

4.  **환경 변수 설정**
    *   `.env` 파일을 프로젝트 루트에 생성하고 필요한 설정을 추가합니다 (기본값으로 `config.py`에 설정되어 있어 개발 단계에서는 생략 가능).
    *   `FLASK_APP=run.py`
    *   `FLASK_ENV=development`

5.  **데이터베이스 초기화**
    ```bash
    flask db upgrade
    ```
    *   이 명령어를 실행하면 `eroom.db` (SQLite) 파일이 생성되고 테이블이 초기화됩니다.

## 2. 프로그램 실행 (Running)

### 일반 실행
```bash
python run.py
```
*   실행 후 브라우저에서 `http://localhost:5000`으로 접속합니다.

### Docker 실행 (컨테이너)
```bash
docker-compose up --build
```
*   Docker를 통해 격리된 환경에서 실행할 수 있습니다.

## 3. 사용 설명서 (User Manual)

### A. 일반 사용자 (Public)
1.  **메인 페이지**: 이룸 스튜디오의 소개, 혜택, 이용 절차를 확인할 수 있습니다.
2.  **지점 안내**: 각 지점의 위치와 시설 정보를 확인하고, '자세히 보기'를 통해 룸 목록을 볼 수 있습니다.
3.  **룸 상세**: 각 연습실의 상세 정보(가격, 장비, 도면 위치)를 확인하고 계약을 신청할 수 있습니다.

### B. 회원 (Member)
1.  **로그인/회원가입**:
    *   우측 상단 '로그인' 버튼을 클릭합니다.
    *   'Login with Kakao' 버튼을 눌러 로그인합니다 (현재는 모의 로그인으로 동작하며, 랜덤 계정이 생성됩니다).
    *   최초 로그인 시 '신규 유저' 또는 '기존 세입자' 선택 온보딩이 진행됩니다.
2.  **마이페이지 (대시보드)**:
    *   로그인 후 우측 상단 '마이페이지'로 접속합니다.
    *   **내 계약 정보**: 현재 이용 중인 방과 계약 기간을 확인합니다.
    *   **빠른 작업**: 수리 요청, 비품 신청, 연장 신청, 퇴실 신청을 바로 할 수 있습니다.
    *   **요청 내역**: 내가 보낸 요청의 처리 상태(접수/처리중/완료)를 실시간으로 확인합니다.

### C. 관리자 (Admin)
1.  **관리자 접속**:
    *   주소창에 `http://localhost:5000/admin`을 입력하여 접속합니다.
    *   (참고: 실제 운영 시에는 관리자 권한이 있는 계정만 접근 가능하도록 설정됩니다.)
2.  **대시보드**:
    *   **통계**: 총 방 수, 가동률, 활성 계약 수, 월 매출 등을 한눈에 확인합니다.
    *   **차트**: 매출 추이 및 방 상태 분포를 시각적으로 확인합니다.
3.  **계약 관리 (Contracts 탭)**:
    *   사용자가 신청한 계약 목록을 확인합니다.
    *   '승인' 또는 '거절' 버튼을 눌러 계약 상태를 변경합니다.
4.  **요청 관리 (Requests 탭)**:
    *   사용자가 보낸 수리/비품 등의 요청을 확인합니다.
    *   '처리중', '완료' 버튼을 눌러 상태를 업데이트합니다.

## 4. 문제 해결 (Troubleshooting)

*   **DB 관련 오류**: `flask db upgrade`를 다시 실행해 보세요.
*   **MySQL 드라이버 오류**: 현재 개발 환경 호환성을 위해 `config.py`에서 SQLite를 강제 사용하도록 설정되어 있습니다. 프로덕션 배포 시에는 MySQL/PostgreSQL 설정을 활성화해야 합니다.
