# Eroom-Studio Web Management System — Full Specification Document (v2.0 / Ultra Detailed)

## 0. 문서 구성
- 서비스 개요
- 사용자 정의 및 온보딩 로직
- 전체 서비스 흐름도
- 퍼블릭 화면 상세 기획
- 로그인/온보딩 UI & 로직 상세
- 계약자 대시보드 상세 기획
- 신청/접수 시스템 상세
- 관리자 시스템 전체 기획
- 데이터 모델(ERD 개념 레벨)
- 상태 정의(계약/방/요청)
- 카카오 로그인 & 알림톡 정책
- 보안/권한 전략
- 기술 구조(Flask 기준)
- 향후 확장 고려 사항

## 1. 서비스 개요
### 1.1 서비스 목적
Eroom-Studio는 지점·방·계약·고장 접수·입주관리·행정요청 등을 하나의 웹 플랫폼에서 처리하는 월단위 연습실 관리 시스템이다.

### 핵심 제공 기능
- 웹 기반 계약 신청 & 자동 계산  
- 기존 오프라인 계약자의 온라인 계정 매핑  
- 사용자의 신청(고장·봉투·배터리·퇴실·연장) 자동 처리  
- 지점/방/계약/사용자 관리  
- 카카오 알림톡 기반의 모든 알림 자동화  
- 모바일 퍼스트 전면 UI  

## 2. 사용자 정의 & 상태 모델
### 2.1 사용자 유형
| 유형 | 설명 |
|------|------|
| 퍼블릭 | 로그인 전. 정보 열람만 가능 |
| 신규 로그인 사용자 | 온보딩 전. 신규인지 기존 계약자인지 선택 필요 |
| 신규 사용자 | 기존 계약 없음. 계약 신청 가능 |
| 기존 계약자(승인 대기) | 오프라인 계약 보유. 계정-계약 연결 승인 대기 |
| 신규 계약 신청자(승인 대기) | 사이트에서 방 선택 후 계약 신청한 상태 |
| 활성 계약 사용자 | 계약 승인됨. /my/room 대시보드 사용 |

### 2.2 사용자 상태값 (user.onboarding_status)
| 값 | 의미 |
|------|------|
| not_started | 첫 로그인. 웰컴 모달 표시 |
| new_user_done | 신규 사용자 온보딩 완료 |
| existing_pending | 기존 계약자 연결 요청 후 승인 대기 |
| existing_linked | 기존 계약자가 관리자에 의해 계정 매핑 완료 |

## 3. 전체 서비스 흐름도 (텍스트 버전)
퍼블릭 → 지점 → 방 상세  
→ 계약 신청 시 카카오 로그인  
→ 웰컴 모달  
→ 신규/기존 선택  
→ /my/room  

상태별 화면: existing_pending / requested / active

## 4. 퍼블릭 화면 상세
### 4.1 Root(/)
- Hero 영역  
- 경쟁력 4카드  
- 사용 절차 Step UI  
- 지점 목록(6개)

### 4.2 지점 상세(/branches/{id})
- 지점 소개  
- 공용시설  
- 지도/위치  
- 도면 기반 방 선택 UI  
- 방 리스트 제공  

### 4.3 방 상세(/rooms/{id})
- 방 사진  
- 기본 정보  
- 가격 정보  
- 계약 신청 폼(시작일·개월·자동 계산)  
- 로그인 여부에 따른 CTA 변경  

## 5. 웰컴 모달 및 온보딩 로직
### Step 1
- 신규 / 기존 선택  
- 신규 → new_user_done  
- 기존 → Step2  

### Step 2(기존 계약자)
- 지점 선택  
- 방 선택  
- 메모  
- 요청 저장 후 existing_pending  

## 6. /my/room 대시보드
### 상태별 메인 화면
- existing_pending : 승인 대기  
- contract.requested : 신규 계약 대기  
- active : 정상 대시보드  

### 구성
- 계약 정보 카드  
- 주요 기능 버튼(연장/퇴실/고장/봉투/배터리)  
- 공지사항  
- 나의 신청 내역  

## 7. 신청/접수 시스템 상세
### 공통 테이블: requests

#### 고장접수
- repair_item  
- description  
- status  

#### 봉투·배터리
- qty  
- status  

#### 연장
- 추가 개월  
- status  

#### 퇴실
- 퇴실희망일  
- status  

## 8. 관리자 시스템
### 관리자 대시보드
- 지표  
- 공실  
- 신규 신청 목록  

### 지점 관리
- 지점 CRUD  
- 공용시설 설정  
- 도면 업로드  

### 방 관리
- 방 CRUD  
- 설비 설정  
- 방 상태 변경  

### 계약 관리
- 승인/반려  
- 연장/퇴실 처리  

### 기존 계약자 계정 연결 요청 관리
- 요청 목록  
- 승인/반려  

### 신청 처리
- 고장/봉투/배터리/퇴실  

## 9. 데이터 모델(개념 ERD)
- users 1:N contracts  
- users 1:N requests  
- branches 1:N rooms  
- rooms 1:N contracts  
- contracts 1:N requests  
- users 1:N tenant_room_link_requests  

## 10. 상태 정의
### contract.status
requested / approved / active / extend_requested / terminate_requested / terminated / cancelled

### room.status
available / reserved / occupied / maintenance

### request.status
submitted / processing / done

## 11. 카카오 알림톡 정책
- 계약 신청/승인/반려  
- 기존 계약자 계정 연결  
- 고장/봉투/배터리/퇴실 처리  

## 12. 권한 & 보안
- user / manager / admin  
- JWT 기반 보호  

## 13. 기술 구조 (Flask)
```
/app
  /routes
  /services
  /models
  /static
  /templates
```

