# 이룸 스튜디오 데이터·UI 연결 흐름 감사

기준일: 2026-11-06 (Asia/Seoul). 대상: 현재 로컬 작업본. 오늘 수정한 퇴실 정산 코드와 기존 미커밋 변경을 포함합니다. 운영 배포본과 동일한지는 확인하지 않았습니다.

실제 재현/브라우저 확인 및 원인 추적을 거쳐 **31개 문제**를 정리했습니다. 우선순위: P0 2개, P1 14개, P2 15개. 별도로 배포 구성 위험 2개를 정적 확인했습니다. 발견 건수는 완전 무결성을 보증하는 수치가 아닙니다.

## 점검 범위와 증거

- 전체 라우트 목록 89개를 수집하고 GET 44개를 격리 환경에서 조회했습니다. 40개는 200, 2개는 필수 파라미터 누락에 따른 400, 1개는 로컬 카카오 설정 미구성 500, 1개는 구형 월세 페이지의 템플릿 누락 500입니다. 카카오 실제 인증은 수행하지 않았습니다.
- 메모리 SQLite DB에서 32개 시나리오를 실행했습니다. 정상 월세 신청→관리자 승인→전자서명→납부 체크→계약서 조회는 통과했고 타인 계약서 접근은 403이었습니다.
- 실제 Flask 화면과 API를 Chrome에서 연결해 데스크톱/390px 모바일 화면 33개를 캡처했습니다. 추가로 세션 만료, 로그인 복귀, 시간제 확인창, 월말 이동을 검사했습니다. 검사한 캡처에서 문서 전체 가로 넘침은 없었습니다.
- JS 파일 10개의 문법 검사를 통과했습니다. 이 결과는 데이터가 들어갈 때 발생하는 런타임 오류가 없다는 뜻은 아닙니다.
- 실제 운영 DB·파일을 변경하거나 문자를 발송하지 않았습니다. 문자 공급자는 mock으로 대체하고 업로드는 감사 폴더의 임시 파일만 사용했습니다.

| 기능 | 확인 범위 | 확인 수준 |
|---|---|---|
| 인증·회원 | 정상 이메일 로그인/가입, 계정 연결, 권한, 만료 세션 | API 재현 + 실제 브라우저 |
| 지점·방 | 공개 조회/상태, 지점·층·방 생성/수정/위치/삭제, 이미지 업로드/삭제 | API/DB 재현 + 공개/관리자 화면 |
| 월세 계약 | 신청, 쿠폰, 중복 기간, 승인/거절, 서명, 계약서, 미매핑 계약 | API/DB 재현 + 화면 금액 비교 |
| 시간제 예약 | 예약 현황, 시간 중복, 시간/가격, 확인창 | API/DB 재현 + 브라우저 콘솔/확인창 |
| 연장·퇴실 | 요청/승인/재처리/후속 계약 충돌/반려·취소, 화면 갱신 | 기존 회귀 증거 + 추가 API/브라우저 |
| 요청·문의 | 접수, 지점·방 연결, 답변 진입점, 구형 요청 폼 | API/DB 재현 + 메뉴 확인 |
| 월세·할인 | 월별 납부, 추가 할인, 퇴실 신청 상태, 월 이동, 문자 컨텍스트 | API/DB + 브라우저 |
| 문자·배치 | 템플릿/로그 조회, 미납 컨텍스트, 실패 재시도, 만료 시 공실 | mock 공급자 재현 + 코드 추적 |
| UI·내비게이션 | 전체 관리자 탭, 로그인 복귀, 빈 상태, 모바일, 모달/Escape | 브라우저 |
| 운영 구성 | Docker 시작 명령, 필수 의존성, migration 대 현재 모델 | 정적 확인; 실제 재배포 미실행 |

## 발견 목록

P0는 인증·계약 소유권에 대한 즉시 조치 대상, P1은 계약/금액/운영 데이터 흐름에 직접 영향을 주는 문제, P2는 특정 기능 실패·상태 표시·UI 연결 문제입니다.

### A01 · P0 · 인증 없이 고정 계정 토큰 발급

테스트 로그인 API에 환경 제한과 인증이 없습니다. 격리 DB에서 무인증 요청으로 관리자 토큰을 받고 관리자 통계까지 200으로 조회했습니다. 운영 id=1/2의 실제 권한은 확인하지 않았지만, 고정 계정 사칭 경로 자체가 열려 있습니다.

- 근거: `AUTH_MOCK_ADMIN`. 위치: [app/routes/auth.py:109](C:/workspace/Eroom-Studio/app/routes/auth.py:109).
- 수정 방향: 운영에서 mock 로그인 라우트를 제거하고 고정 계정 토큰 발급을 차단합니다.

### A02 · P0 · 본인 확인 없이 기존 계약 자동 연결

회원가입 시 입력한 전화번호/이메일만 일치하면 미매핑 계약의 소유자가 새 계정으로 바뀝니다. 격리 계약이 새 가입자에게 연결되는 것을 확인했습니다.

- 근거: `AUTH_PHONE_CLAIM`. 위치: [app/services/contract_mapping_service.py:23](C:/workspace/Eroom-Studio/app/services/contract_mapping_service.py:23).
- 수정 방향: 확인된 연락처 또는 관리자 승인에 한해 계약을 연결합니다.

### A03 · P1 · 쿠폰 계약 하나로 계약 목록 전체 500

Coupon 모델에 없는 name을 계약 API가 읽습니다. 쿠폰 적용 신청은 201인데 사용자 계약 목록, 관리자 계약 목록, 관리자 상세가 모두 AttributeError로 500입니다.

- 근거: `COUPON_CONTRACT_LISTS`. 위치: [app/routes/contract.py:417](C:/workspace/Eroom-Studio/app/routes/contract.py:417).
- 수정 방향: 실제 쿠폰 필드와 응답 계약을 통일하고 쿠폰 계약을 포함한 전체 목록 회귀 테스트를 추가합니다. 관리자 동일 참조는 admin.py:404,467입니다.

### A04 · P1 · 퇴실 신청 중인 계약이 중복 예약 검사에서 제외

기존 계약이 terminate_requested이면 기간이 겹치는 새 계약도 201로 생성되어 같은 방에 겹치는 계약 2개가 생깁니다.

- 근거: `BOOKING_PENDING_TERMINATION_OVERLAP`. 위치: [app/routes/contract.py:175](C:/workspace/Eroom-Studio/app/routes/contract.py:175).
- 수정 방향: 진행 중인 계약 상태 집합을 통일하고 승인되지 않은 퇴실 예정일로 기존 점유를 조기에 해제하지 않도록 합니다.

### A05 · P1 · 연장 요청 재처리 때 계약 기간이 다시 연장

동일 요청을 done으로 두 번 처리하면 종료일이 2027-02-28에서 2027-03-28로 다시 늘어납니다. 완료 건에 답변을 추가할 때도 같은 경로를 탑니다.

- 근거: `EXTENSION_REPLAY`. 위치: [app/routes/admin.py:995](C:/workspace/Eroom-Studio/app/routes/admin.py:995).
- 수정 방향: 처리 전 상태를 확인하고 연장 부수 효과를 한 번만 실행합니다. 답변 수정과 승인 처리를 분리합니다.

### A06 · P1 · 연장 승인과 다음 입주 계약의 기간 충돌

다음 계약이 2027-02-01부터 존재해도 기존 계약을 2027-02-28까지 연장하는 요청이 200으로 승인됩니다.

- 근거: `EXTENSION_FUTURE_CONTRACT_OVERLAP`. 위치: [app/routes/admin.py:1000](C:/workspace/Eroom-Studio/app/routes/admin.py:1000).
- 수정 방향: 연장 승인에서도 같은 방의 후속 계약과 기간 중복을 검증합니다.

### A07 · P1 · 시간제 금액을 서버에서 일관되게 확정하지 않음

시간당 10,000원, 3시간 예약에서 계약 price는 30,000원인데 initial_payment와 첫 달 스냅샷은 10,000원입니다. 같은 시간 범위에 hours=0을 보내면 price=0도 저장됩니다.

- 근거: `PRICING_HOURLY_FIRST_PAYMENT / PRICING_HOURLY_CLIENT_HOURS`. 위치: [app/routes/contract.py:305](C:/workspace/Eroom-Studio/app/routes/contract.py:305).
- 수정 방향: 서버가 시작·종료 시간으로 이용 시간을 계산하고 응답·계약·스냅샷 금액을 동일 계산 결과에서 만듭니다.

### A08 · P1 · 기간·금액 입력 검증 누락

months=-1인 신청이 201로 저장되어 종료일이 시작일보다 앞섭니다. 50만원 방에 90만원 쿠폰을 적용하면 월요금과 첫 결제액 -40만원도 저장됩니다.

- 근거: `CONTRACT_INVALID_DURATION / PRICING_NEGATIVE_RENT`. 위치: [app/routes/contract.py:171](C:/workspace/Eroom-Studio/app/routes/contract.py:171).
- 수정 방향: 양의 계약 기간과 유효한 날짜/시간 범위를 검증하고 할인 후 금액 하한을 보장합니다.

### A09 · P1 · 미매핑 계약 생성 API가 항상 모델 오류

필수 값을 채운 정상 요청이 500입니다. Contract 모델에 없는 total_price 인자를 생성자에 넘깁니다.

- 근거: `UNMAPPED_CREATE`. 위치: [app/routes/admin.py:1674](C:/workspace/Eroom-Studio/app/routes/admin.py:1674).
- 수정 방향: 현재 계약 모델의 price/deposit 필드로 입력과 응답을 맞춥니다.

### A10 · P1 · 계약 상태와 공실 표시가 서로 어긋남

신청 완료 뒤에도 공개 방 상태가 available입니다. 야간 만료 처리도 후속 waiting_signature 계약이 있는 방을 available로 만듭니다. 두 경우 모두 공개 화면이 실제 계약 상태와 다릅니다.

- 근거: `ROOM_STATUS_AFTER_APPLY / BATCH_FUTURE_RESERVATION_STATUS`. 위치: [app/tasks.py:46](C:/workspace/Eroom-Studio/app/tasks.py:46).
- 수정 방향: 계약 생성·만료 처리 후 Room.sync_status를 일관되게 사용하고 예약/점검 상태를 보존합니다. 신청 생성의 누락은 contract.py:354입니다.

### A11 · P1 · 퇴실 신청만 해도 월세 관리에서 사라짐

이용 종료 전 terminate_requested 계약이 월세 관리 목록과 월별 납부 API에서 모두 제외됩니다. 관리자가 잔여 이용 기간의 납부를 확인하기 어렵습니다.

- 근거: `RENT_PENDING_TERMINATION_DISAPPEARS`. 위치: [app/routes/admin.py:322](C:/workspace/Eroom-Studio/app/routes/admin.py:322).
- 수정 방향: 점유가 유지되는 퇴실 신청 계약을 납부 대상에 포함하고 조회월과 계약 기간으로 필터링합니다.

### A12 · P1 · 실패한 문자 재시도가 성공으로 취급됨

첫 발송은 공급자 오류로 실패했는데 같은 건 재시도는 True/Skipped(Duplicate)를 반환합니다. 공급자 호출은 총 1회뿐입니다. 자동 업무가 발송 성공으로 오인할 수 있습니다.

- 근거: `SMS_FAILED_RETRY`. 위치: [app/utils/sms_service.py:177](C:/workspace/Eroom-Studio/app/utils/sms_service.py:177).
- 수정 방향: 성공한 발송만 중복 차단하고 FAILED 상태에는 명시적인 재시도 흐름을 둡니다.

### A13 · P1 · 매월 쿠폰의 화면 요금과 서버 요금 불일치

실제 방 화면에서 매월 1만원 쿠폰 적용 후 서버는 49만원인데 화면 월 납부액은 50만원입니다. 프런트는 every_month를 비교하고 서버/모델은 monthly를 사용합니다.

- 근거: `MONTHLY_COUPON_UI`. 위치: [app/templates/public/room_detail.html:1028](C:/workspace/Eroom-Studio/app/templates/public/room_detail.html:1028).
- 수정 방향: 쿠폰 주기 값을 통일하고 화면이 서버의 최종 계산값을 표시하도록 합니다. EXCLUSIVE 정책도 같은 방식으로 반영합니다.

### A14 · P2 · 쿠폰 사용 횟수가 중복 증가하고 미적용 쿠폰도 차감

무제한 쿠폰으로 계약 1건을 신청하면 used_count가 2가 됩니다. 최소 12개월 쿠폰을 2개월 계약에 보내도 할인은 적용되지 않으면서 사용 횟수는 2가 됩니다.

- 근거: `COUPON_UNLIMITED_COUNT / COUPON_INVALID_CONSUMED`. 위치: [app/routes/contract.py:220](C:/workspace/Eroom-Studio/app/routes/contract.py:220).
- 수정 방향: 검증을 통과해 실제 적용된 쿠폰만 트랜잭션 안에서 원자적으로 한 번 증가시킵니다.

### A15 · P2 · 퇴실 신청 후 계약 화면이 갱신되지 않음

성공 응답 뒤 서버는 terminate_requested인데 같은 화면의 계약 객체는 active입니다. 계약/보증금 표시와 신청 버튼이 새로고침 전까지 이전 상태로 남습니다.

- 근거: `TERMINATION_UI_REFRESH`. 위치: [app/templates/user/dashboard.html:987](C:/workspace/Eroom-Studio/app/templates/user/dashboard.html:987).
- 수정 방향: 성공 시 요청 목록뿐 아니라 계약 목록도 다시 조회하거나 응답으로 상태를 동기화합니다.

### A16 · P2 · 방 문의의 지점·호실 연결 유실

방 상세에서 쓰는 room_id 형식의 문의를 접수하면 관리자 목록 room_name=N/A, branch_id=null입니다. 시간제 문의는 room_name 문자열만 보내 지점 필터 연결이 여전히 없습니다.

- 근거: `INQUIRY_ROOM_ASSOCIATION`. 위치: [app/routes/admin.py:739](C:/workspace/Eroom-Studio/app/routes/admin.py:739).
- 수정 방향: 검증한 room_id를 기준으로 호실·지점 관계를 서버에서 해석해 저장/반환합니다.

### A17 · P1 · 요청·문의 접수와 관리/답변 열람 사이에 진입점 없음

관리자 사이드바에서 요청·문의 메뉴가 양쪽 레이아웃 모두 필터로 제거됩니다. 사용자 요청 목록/답변 화면도 주석 처리되어 있습니다. API와 숨은 화면은 있어도 정상 메뉴 동선으로 접수 결과·답변을 확인하기 어렵습니다.

- 근거: `HIDDEN_REQUEST_NAV + 화면 코드 확인`. 위치: [app/templates/admin/partials/sidebar.html:40](C:/workspace/Eroom-Studio/app/templates/admin/partials/sidebar.html:40).
- 수정 방향: 지원하는 요청 유형에 대응하는 관리자 처리 메뉴와 사용자 진행/답변 조회 동선을 연결합니다. 사용자 화면은 dashboard.html:44,504입니다.

### A18 · P2 · 특정 월 할인과 납부 관리 금액이 다름

50만원 계약에 해당 월 10만원 할인을 저장하면 문자 컨텍스트는 40만원인데 월세 관리 API/화면은 계속 50만원입니다.

- 근거: `CUSTOM_DISCOUNT_AND_RENT_AMOUNT`. 위치: [app/routes/admin.py:321](C:/workspace/Eroom-Studio/app/routes/admin.py:321).
- 수정 방향: 조회월별 할인 적용 전/후 금액을 공통 계산해 납부 화면·문자·통계에서 사용합니다.

### A19 · P1 · 선택한 월과 다른 월로 미납 문자 생성

과거 2026-10월에 대한 문자를 요청해도 서버 컨텍스트는 현재 2026-11월로 계산됩니다. 실제 화면도 조회월을 전송하지 않습니다.

- 근거: `RENT_SELECTED_MONTH_SMS`. 위치: [app/templates/admin/partials/tab_rent_management.html:407](C:/workspace/Eroom-Studio/app/templates/admin/partials/tab_rent_management.html:407).
- 수정 방향: 조회월을 요청에 포함하고 서버가 그 월의 납부일·할인·미납 여부를 검증해 컨텍스트를 만듭니다.

### A20 · P2 · 이력이 있는 사용자·방 삭제가 500

문의 이력이 있는 사용자를 삭제하면 requests.user_id NOT NULL 오류, 종료 계약 이력이 있는 방을 삭제하면 contracts.room_id NOT NULL 오류입니다. 활성 계약 유무만 검사해 이력 관계를 놓칩니다.

- 근거: `USER_DELETE_WITH_REQUEST_HISTORY / ROOM_DELETE_WITH_HISTORY`. 위치: [app/routes/admin.py:1824](C:/workspace/Eroom-Studio/app/routes/admin.py:1824).
- 수정 방향: 이력 보존 정책에 맞춰 삭제를 차단하고 명확한 4xx를 반환하거나 보관 처리를 사용합니다. 방 삭제는 admin.py:1439입니다.

### A21 · P2 · 임시 계정의 기존 입주자는 본인 번호로 가입 불가

임시 계정에 저장된 전화번호로 정식 가입하면 중복 번호 400이 먼저 반환되어 뒤의 임시 계약 재매핑 로직까지 도달하지 못합니다.

- 근거: `AUTH_PLACEHOLDER_REGISTRATION`. 위치: [app/routes/auth.py:158](C:/workspace/Eroom-Studio/app/routes/auth.py:158).
- 수정 방향: 본인 확인 후 임시 계정 전환/연결을 수행하는 별도 흐름을 제공합니다.

### A22 · P2 · 구형 온보딩·요청 페이지의 연결 단절

기존 입주자 버튼은 존재하지 않는 /onboarding/link로 가서 404입니다. /requests/new는 contract_id 없이 연장을 보내고, 서버는 201 접수와 200 완료를 반환하지만 변경할 계약이 없습니다. 구형 /admin/rent-management는 없는 템플릿으로 500입니다.

- 근거: `MISSING_PAGES / REQUEST_EXTENSION_WITHOUT_CONTRACT`. 위치: [app/templates/user/onboarding.html:54](C:/workspace/Eroom-Studio/app/templates/user/onboarding.html:54).
- 수정 방향: 사용 중인 새 흐름으로 연결하거나 구형 진입점을 제거/리다이렉트합니다. 계약이 필요한 요청은 계약 ID를 필수로 검증합니다.

### A23 · P2 · 세션 만료가 계약 없음처럼 보임

잘못된 토큰으로 마이페이지 진입 시 API 401을 받지만 페이지에 남아 진행 중인 계약이 없습니다를 표시합니다. 공통 헤더가 토큰은 지우지만 재로그인 동선을 실행하지 않습니다.

- 근거: `USER_EXPIRED_SESSION_VALID`. 위치: [app/templates/user/dashboard.html:877](C:/workspace/Eroom-Studio/app/templates/user/dashboard.html:877).
- 수정 방향: 401을 빈 데이터와 구별하고 재로그인 안내/원래 페이지 복귀를 처리합니다.

### A24 · P2 · 로그인 후 신청하던 방으로 돌아가지 않음

/login?next=/rooms/4에서 정상 로그인했는데 /my/room으로 이동합니다. 방 화면은 next를 붙여 보내지만 로그인 화면은 사용하지 않습니다.

- 근거: `LOGIN_NEXT_IGNORED`. 위치: [app/templates/user/login.html:164](C:/workspace/Eroom-Studio/app/templates/user/login.html:164).
- 수정 방향: 동일 사이트 내부의 안전한 next 경로를 검증해 복귀시킵니다.

### A25 · P2 · 관리자 일부 탭은 새로고침 시 초기화

회원 관리에서 새로고침하면 URL은 #users인데 화면은 dashboard입니다. 쿠폰·문자·월세 등도 해시 복원 허용 목록에서 빠져 있습니다.

- 근거: `ADMIN_RELOAD_TAB`. 위치: [app/static/js/admin/app.js:18](C:/workspace/Eroom-Studio/app/static/js/admin/app.js:18).
- 수정 방향: 사용 가능한 탭 목록과 해시 저장/복원 목록을 하나로 통일합니다.

### A26 · P2 · 시간제 확인창에 월세 항목과 변수 오류

시간제 페이지에서 월요금 전용 변수를 참조해 basePrice 등 6종의 ReferenceError가 발생합니다. 확인창에 기본 월요금/첫 달 결제액/이후 월 납부액 등 불필요한 빈 항목도 생성됩니다.

- 근거: `HOURLY_CONFIRMATION + 실제 페이지 콘솔`. 위치: [app/templates/public/contract_confirm_modal.html:89](C:/workspace/Eroom-Studio/app/templates/public/contract_confirm_modal.html:89).
- 수정 방향: 월세·시간제 정산 영역을 조건부 렌더링하거나 각 폼의 명시적인 가격 요약 데이터로 구성합니다.

### A27 · P2 · 이미지 없는 지점의 빈 상태와 구형 클릭 코드 오류

신규 지점의 image_url=None이 문자열 None으로 삽입되어 /branches/None 404를 요청합니다. 같은 페이지는 없는 contractBtn에 addEventListener를 호출해 TypeError도 냅니다.

- 근거: `branch / mobile-branch 브라우저 콘솔·네트워크`. 위치: [app/templates/public/branch_detail.html:104](C:/workspace/Eroom-Studio/app/templates/public/branch_detail.html:104).
- 수정 방향: 값을 JSON으로 안전하게 넘기고 빈 이미지 fallback을 적용합니다. 제거된 버튼의 잔존 이벤트 연결(branch_detail.html:461)을 정리합니다.

### A28 · P2 · 이미지 업로드·삭제가 다른 이미지 표시를 깨뜨림

같은 이름으로 사진을 두 번 올리면 DB 행은 2개인데 URL/파일이 같습니다. 한 장 삭제 시 다른 행의 파일도 사라집니다. 지점 대표 사진 삭제 후에도 branch.image_url은 삭제된 URL로 남습니다.

- 근거: `IMAGE_SAME_NAME_OVERWRITE / BRANCH_MAIN_IMAGE_DELETE`. 위치: [app/routes/admin.py:1567](C:/workspace/Eroom-Studio/app/routes/admin.py:1567).
- 수정 방향: 각 업로드에 고유 파일명을 부여하고 삭제 시 대표 사진과 참조 관계를 함께 갱신합니다. 지점 삭제 처리는 admin.py:1346입니다.

### A29 · P2 · 계약 모달의 키보드·보조기술 동작 미완성

열린 계약 상세에서 Escape가 닫기 동작을 하지 않습니다. role=dialog, aria-modal도 없고 모달로 포커스를 이동시키는 처리도 없습니다. 화면의 아이콘 전용 버튼 다수에 접근성 이름이 없습니다.

- 근거: `MODAL_ACCESSIBILITY / MODAL_ESCAPE / SCREEN 검사`. 위치: [app/templates/admin/partials/tab_contracts.html:644](C:/workspace/Eroom-Studio/app/templates/admin/partials/tab_contracts.html:644).
- 수정 방향: 모달의 포커스 이동·복귀, 포커스 제한, Escape 닫기와 적절한 접근성 속성/버튼 이름을 적용합니다.

### A30 · P2 · 월말에 다음 달 버튼이 한 달을 건너뜀

월세 관리 currentDate=2026-01-31에서 다음 달을 누르면 2026-02가 아니라 2026-03으로 이동합니다. Date.setMonth가 말일을 다음 달로 넘기는 동작 때문입니다.

- 근거: `RENT_MONTH_END_NAV`. 위치: [app/templates/admin/partials/tab_rent_management.html:299](C:/workspace/Eroom-Studio/app/templates/admin/partials/tab_rent_management.html:299).
- 수정 방향: 월 이동 전에 일자를 1일로 고정하거나 연/월 값만 관리합니다.

### A31 · P1 · 서명 거절 API가 이미 이용 중인 계약도 거절로 바꿈

active 계약에 서명 거절 요청을 보내면 200으로 signature_rejected가 됩니다. 방은 occupied로 남아 계약과 방 상태가 분리됩니다. 서명 API와 달리 거절 API에는 허용 상태 검사도 없습니다.

- 근거: `SIGNATURE_REJECTION_ACTIVE_CONTRACT`. 위치: [app/routes/contract.py:494](C:/workspace/Eroom-Studio/app/routes/contract.py:494).
- 수정 방향: 서명 대기 등 허용된 상태에서만 거절을 처리하고 방 상태를 함께 동기화합니다.

## 별도 정적 확인: 재배포/스키마 위험

- **O01 · P1 · Docker 실행 의존성 누락**: [Dockerfile:15](C:/workspace/Eroom-Studio/Dockerfile:15)는 gunicorn으로 실행하지만 [requirements.txt:1](C:/workspace/Eroom-Studio/requirements.txt:1)에 gunicorn이 없습니다. 직접 import하는 flask_apscheduler, pytz, dateutil도 명시되어 있지 않습니다. 현재 격리 테스트는 기존 로컬 의존성을 사용했으므로 새 컨테이너 빌드 성공을 검증한 것이 아닙니다. 새 환경의 설치 목록과 실행 명령을 맞추고 깨끗한 이미지에서 기동 검증이 필요합니다.
- **O02 · P1 · migration으로 현재 모델 재현 불가**: [migrations/versions/120af649950d_initial_migration.py:63](C:/workspace/Eroom-Studio/migrations/versions/120af649950d_initial_migration.py:63)는 contracts.total_price를 생성합니다. 현재 모델은 price/deposit 및 다수의 정산/증거 필드를 쓰고 coupons, sms_templates, sms_logs, custom_discounts 등도 사용하지만 커밋된 migration 4개에 이 테이블들의 생성/필드 전환이 없습니다. 실제 운영 DB에 수동 변경이 있는지는 확인하지 않았습니다. 운영 스키마를 읽어 대조한 뒤 데이터 보존 migration을 준비해야 합니다.

## 정책/환경 확인이 필요한 사항

- 미래 입실 계약을 서명 즉시 active/occupied로 바꾸고 납부 목록에도 넣습니다. 이 상태 정의가 의도인지, 실제 입실 전 문자·매출 집계에 포함되어야 하는지는 별도 정책 확인이 필요합니다. 이 건은 확정 오류 수에 넣지 않았습니다.
- 월세의 자동 연장/중도퇴실 위약금/보증금 공제 기준은 서로 다른 화면·계약 문구와 대조할 필요가 있습니다. 오늘 정산 표시는 기존 월 임대료 1개월 규칙을 사용하며 새로운 정책을 확정한 것이 아닙니다.
- 실제 카카오 인증, 문자 공급자 전달/비용/잔액, 운영 MySQL 스키마·트랜잭션·동시 예약 경합, 외부 결제, 재시작/다중 워커 배치 동작은 미검증입니다. 클린 배포와 실제 계정 기반 검증이 남아 있습니다.
- 과거 백업 템플릿은 실제 라우팅 대상이 아니므로 UI 점검 대상에서 제외했습니다. mule-crawler 실행/배포도 이번 웹사이트 동선 점검 범위에 포함하지 않았습니다.

## 수정 순서 제안

1. A01·A02 인증/계약 소유권 경계 차단.
2. A03·A04·A05·A06·A07·A08·A31: 계약 조회 장애, 중복 계약, 중복 연장, 가격/상태 검증.
3. A09~A19: 미매핑 등록, 방/납부 상태, 문자 재시도/조회월, 쿠폰 표시/카운트, 접수·처리 동선.
4. A20~A30: 삭제/이력 정책, 구형 진입점, 세션/로그인 복귀, 모달·모바일·이미지·월 이동.
5. O01·O02를 실제 운영 스키마와 대조해 배포 검증.

이번 요청에서는 조사와 증거·보고서 작성만 했습니다. 서비스 소스 수정, 기존 데이터 보정, 운영 배포는 하지 않았습니다.

## 증거 파일

- [API 재현 결과](C:/Users/gnswp/.codex/visualizations/2026/11/06/01a1b08d-1f1d-7950-b8eb-a70458d4514e/site-audit/api-results.json)
- [GET 스모크 결과](C:/Users/gnswp/.codex/visualizations/2026/11/06/01a1b08d-1f1d-7950-b8eb-a70458d4514e/site-audit/smoke.json)
- [전체 라우트 목록](C:/Users/gnswp/.codex/visualizations/2026/11/06/01a1b08d-1f1d-7950-b8eb-a70458d4514e/site-audit/routes.json)
- [브라우저 결과](C:/Users/gnswp/.codex/visualizations/2026/11/06/01a1b08d-1f1d-7950-b8eb-a70458d4514e/site-audit/browser-results.json)
- [세션·로그인·시간제·월말 추가 결과](C:/Users/gnswp/.codex/visualizations/2026/11/06/01a1b08d-1f1d-7950-b8eb-a70458d4514e/site-audit/browser-followup.json)
- [재현 스크립트](C:/Users/gnswp/.codex/visualizations/2026/11/06/01a1b08d-1f1d-7950-b8eb-a70458d4514e/site-audit/audit.py)
- [브라우저 스크립트](C:/Users/gnswp/.codex/visualizations/2026/11/06/01a1b08d-1f1d-7950-b8eb-a70458d4514e/site-audit/browser.cjs)
- [쿠폰 화면](C:/Users/gnswp/.codex/visualizations/2026/11/06/01a1b08d-1f1d-7950-b8eb-a70458d4514e/site-audit/coupon-ui.png)
- [퇴실 신청 직후 화면](C:/Users/gnswp/.codex/visualizations/2026/11/06/01a1b08d-1f1d-7950-b8eb-a70458d4514e/site-audit/user-after-termination.png)
- [시간제 확인창](C:/Users/gnswp/.codex/visualizations/2026/11/06/01a1b08d-1f1d-7950-b8eb-a70458d4514e/site-audit/hourly-confirmation-visible.png)
- [모바일 월세 관리](C:/Users/gnswp/.codex/visualizations/2026/11/06/01a1b08d-1f1d-7950-b8eb-a70458d4514e/site-audit/mobile-admin-rent-management.png)

브라우저 결과의 초기 USER_EXPIRED_SESSION 항목은 테스트 init script가 유효 토큰을 재주입한 경우여서 세션 만료 근거로 사용하지 않았습니다. 별도 context에서 검증한 browser-followup.json의 USER_EXPIRED_SESSION_VALID를 사용했습니다.

접근성/폼/내비게이션 점검 기준: [Web Interface Guidelines](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md). 일반 권고와 실제 재현 결과는 구분했습니다.
