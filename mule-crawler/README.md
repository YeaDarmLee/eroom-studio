# 뮬(mule.co.kr) 자동화 크롤러

뮬 사이트(https://www.mule.co.kr)에 자동으로 로그인하고 글을 작성하는 Playwright 기반 자동화 스크립트입니다.

## 📋 사전 요구사항

- Python 3.8+
- pip

## 🚀 설치 방법

```bash
# 1. 이 폴더로 이동
cd mule-crawler

# 2. 패키지 설치
pip install -r requirements.txt

# 3. Playwright 브라우저 설치
playwright install chromium

# 4. 환경변수 설정
copy .env.example .env
# .env 파일을 열어서 아이디/비밀번호 입력
```

## ⚙️ 환경변수 설정 (.env)

```env
MULE_ID=여기에_아이디
MULE_PW=여기에_비밀번호
```

## ▶️ 실행 방법

```bash
# 로그인 테스트
python mule_login.py
```

## 📌 주요 특징

| 항목 | 내용 |
|------|------|
| 브라우저 엔진 | Chromium (Playwright) |
| 캡챠 처리 | Cloudflare Turnstile 수동 클릭 지원 |
| 세션 저장 | `session_cookies.json`으로 쿠키 저장 → 재로그인 최소화 |
| 실행 모드 | `headless=False` (브라우저 창 보임) 권장 |

## ⚠️ Cloudflare Turnstile 캡챠 안내

뮬 사이트는 Cloudflare Turnstile 캡챠를 사용합니다.  
스크립트 실행 시 브라우저 창에서 **"사람인지 확인하십시오"** 체크박스를 직접 클릭해야 합니다.

한 번 로그인에 성공하면 `session_cookies.json`에 세션이 저장되어  
다음 실행 시 캡챠 없이 자동 로그인됩니다 (세션 만료 전까지).

## 📂 파일 구조

```
mule-crawler/
├── mule_login.py          # 로그인 핵심 모듈
├── requirements.txt       # 패키지 의존성
├── .env.example           # 환경변수 템플릿
├── .env                   # 실제 환경변수 (gitignore 필요)
└── session_cookies.json   # 저장된 로그인 세션 (자동 생성)
```
