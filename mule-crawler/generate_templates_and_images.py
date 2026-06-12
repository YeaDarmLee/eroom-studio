import os
import json
import urllib.request
import urllib.error
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# .env 파일 로드
load_dotenv()

# 상수 정의
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "template")
RESULT_DIR = os.path.join(BASE_DIR, "result")
API_BASE_URL = os.getenv("API_BASE_URL", "https://eroom-studio.co.kr")

BRANCHES = ["samsung", "hongdae", "incheon", "mokdong", "bongcheon", "bucheon"]

# 로컬 테스트 및 API 실패 시를 위한 Mock 데이터
MOCK_DATA = {
    "samsung": {
        "available_rooms": [
            {"floor": "3층", "name": "7호", "area_pyung": 1.74, "price": 500000, "description": "보컬 및 미디 작업 추천"},
            {"floor": "3층", "name": "14호", "area_pyung": 1.03, "price": 420000, "description": "보컬 및 미디 작업 추천"},
            {"floor": "3층", "name": "15호", "area_pyung": 1.03, "price": 420000, "description": "보컬 및 미디 작업 추천"},
            {"floor": "3층", "name": "16호", "area_pyung": 1.03, "price": 420000, "description": "보컬 및 미디 작업 추천"},
            {"floor": "3층", "name": "19호", "area_pyung": 1.80, "price": 550000, "description": "보컬 및 미디 작업 추천"}
        ],
        "is_fully_occupied": False,
        "next_available_date": None
    },
    "hongdae": {
        "available_rooms": [
            {"floor": "4층", "name": "403호", "area_pyung": 2.50, "price": 600000, "description": "보컬 및 미디 작업 추천"},
            {"floor": "4층", "name": "409호", "area_pyung": 2.50, "price": 600000, "description": "보컬 및 미디 작업 추천"}
        ],
        "is_fully_occupied": False,
        "next_available_date": None
    },
    "incheon": {
        "available_rooms": [
            {"floor": "4층", "name": "401호", "area_pyung": 2.20, "price": 450000, "description": "보컬, 미디, 개인 작업 권장"},
            {"floor": "4층", "name": "403호", "area_pyung": 2.50, "price": 500000, "description": "보컬 및 미디 작업 추천"}
        ],
        "is_fully_occupied": False,
        "next_available_date": None
    },
    "mokdong": {
        "available_rooms": [
            {"floor": "3층", "name": "316호", "area_pyung": 2.13, "price": 530000, "description": "보컬 및 미디 작업 추천"}
        ],
        "is_fully_occupied": False,
        "next_available_date": None
    },
    "bongcheon": {
        "available_rooms": [],
        "is_fully_occupied": True,
        "next_available_date": "2026-07-01"
    },
    "bucheon": {
        "available_rooms": [
            {"floor": "5층", "name": "A", "area_pyung": 4.23, "price": 600000, "description": "보컬, 미디, 개인 악기 연습 권장 (A room)"},
            {"floor": "5층", "name": "B", "area_pyung": 4.23, "price": 800000, "description": "보컬, 미디, 개인 악기 연습 권장 (B room)"},
            {"floor": "5층", "name": "H", "area_pyung": 4.23, "price": 350000, "description": "보컬, 미디, 개인 악기 연습 권장 (H room)"}
        ],
        "is_fully_occupied": False,
        "next_available_date": None
    }
}

def fetch_branch_data(branch):
    """서버 API로부터 지점 정보를 가져옵니다. 실패 시 Mock 데이터를 사용합니다."""
    url = f"{API_BASE_URL}/api/public/branches/{branch}/rooms-status"
    print(f"[{branch.upper()}] API 호출 시도: {url}")
    
    try:
        # 2초 타임아웃으로 API 요청
        req = urllib.request.Request(url, headers={'User-Agent': 'EroomTemplateBuilder/1.0'})
        with urllib.request.urlopen(req, timeout=2.0) as response:
            data = json.loads(response.read().decode('utf-8'))
            print(f"[{branch.upper()}] API 연동 성공!")
            # API 응답 구조에 맞게 파싱 (예: {"status": "success", "data": {...}} 또는 {...} 직접 전달)
            if "data" in data:
                return data["data"]
            return data
    except Exception as e:
        print(f"[{branch.upper()}] API 호출 실패 ({type(e).__name__}: {e}). Mock 데이터를 사용합니다.")
        return MOCK_DATA[branch]

def generate_rooms_html(rooms):
    """공실 목록을 세로형 프리미엄 카드 리스트 마크업으로 변환"""
    cards = []
    for r in rooms:
        price_val = r['price']
        if price_val < 50000:
            price_str = f"<span style='color: #ef4444; font-weight: 800;'>특가 {price_val:,}원</span>"
        else:
            price_str = f"{int(price_val / 10000)}만 원"
            
        desc = r.get('description', '') or '쾌적한 개인 연습 공간'
        desc = desc.replace('\n', ' • ').strip()
        
        cards.append(f"""
          <div
            style="background-color: #FAF8F5; border: 1px solid #EBE7E0; border-radius: 16px; padding: 22px 24px; display: flex; flex-direction: column; gap: 14px; box-shadow: 0 2px 8px rgba(42, 66, 58, 0.03); text-align: left;">
            <div style="display: flex; flex-direction: column; align-items: center; gap: 6px;">
              <span
                style="background-color: #EAE6DF; color: #5C554E; font-size: 15px; font-weight: 800; padding: 6px 0; border-radius: 8px; width: 100%; text-align: center; display: block;">{r['floor']} {r['name']}</span>
            </div>
            <div style="display: flex; flex-direction: column; gap: 8px; border-top: 1px solid #F3EFE9; border-bottom: 1px solid #F3EFE9; padding: 14px 0;">
              <div style="display: flex; align-items: center; font-size: 13.5px; color: #6E675F;">
                <span>실평수: <strong style="color: #2A423A;">약 {r['area_pyung']:.2f}평</strong></span>
              </div>
              <div style="display: flex; align-items: center; font-size: 13.5px; color: #6E675F;">
                <span>추천 용도: <strong style="color: #2A423A;">{desc}</strong></span>
              </div>
              <div style="display: flex; align-items: center; font-size: 13.5px; color: #6E675F;">
                <span>기본 옵션: 개별 디지털 도어락 • 냉난방 에어컨 • 초고속 기가 인터넷</span>
              </div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-size: 12.5px; color: #8C7A6B; font-weight: 600;">월 사용료</span>
              <span style="font-size: 18px; font-weight: 800; color: #2A423A;">{price_str}</span>
            </div>
          </div>
        """)
        
    cards_content = "".join(cards)
    return f"""
        <div style="display: flex; flex-direction: column; gap: 14px;">
          {cards_content}
        </div>
    """

def generate_occupied_html(next_date):
    """만실 시 노출할 미니멀 메시지 박스 마크업"""
    date_str = next_date if next_date else "2026-07-01"
    return f"""
          <div
            style="background-color: #FAF8F5; border: 1px solid #EBE7E0; border-radius: 16px; padding: 35px 24px; text-align: center; color: #7A7267; margin: 0; box-shadow: 0 2px 8px rgba(42, 66, 58, 0.03); display: flex; flex-direction: column; align-items: center; gap: 10px;">
            <div style="font-size: 15px; font-weight: 800; color: #2A423A;">현재 모든 룸이 만실 상태입니다.</div>
            <div style="font-size: 13px; color: #6E675F; border-top: 1px solid #F3EFE9; border-bottom: 1px solid #F3EFE9; padding: 12px 0; width: 100%; max-width: 320px; margin: 4px auto;">
              가장 빠른 입실 가능 예정일: <strong style="color: #8C7A6B; font-weight: 800;">{date_str}</strong>
            </div>
            <div style="font-size: 11.5px; color: #A19B93; line-height: 1.5;">
              * 사전 예약 및 퇴실 예정 대기 신청을 해두시면<br>공실 발생 즉시 우선 연락을 드립니다.
            </div>
          </div>
    """

def build_templates():
    """지점별 HTML 템플릿을 API 기반으로 변환하여 생성합니다."""
    generated_files = {}
    today_str = datetime.now().strftime("%y-%m-%d")
    
    for branch in BRANCHES:
        source_path = os.path.join(TEMPLATE_DIR, f"source_template_{branch}.html")
        dest_path = os.path.join(RESULT_DIR, f"template_{branch}.html")
        
        if not os.path.exists(source_path):
            print(f"[ERROR] 소스 템플릿 파일을 찾을 수 없습니다: {source_path}")
            continue
            
        data = fetch_branch_data(branch)
        rooms = data.get("available_rooms", [])
        is_occupied = data.get("is_fully_occupied", False) or len(rooms) == 0
        next_date = data.get("next_available_date")
        
        # 룸 마크업 생성
        if is_occupied:
            room_section_html = generate_occupied_html(next_date)
        else:
            room_section_html = generate_rooms_html(rooms)
            
        # 소스 파일 읽기
        with open(source_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
            
        # "실시간 이용 가능한 룸" 문구 앞에 오늘 날짜 (YY-MM-DD) 주입
        template_content = template_content.replace("실시간 이용 가능한 룸", f"{today_str} 실시간 이용 가능한 룸")
            
        # 플레이스홀더 치환
        final_content = template_content.replace("<!-- ROOM_SECTION_PLACEHOLDER -->", room_section_html)
        
        # 최종 파일로 쓰기
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
            
        print(f"[SUCCESS] HTML 생성 완료: {dest_path}")
        generated_files[branch] = dest_path
        
    return generated_files

def generate_images(generated_files):
    """Playwright를 구동해 생성된 HTML을 이미지로 캡처합니다."""
    if not generated_files:
        print("[WARNING] 캡처할 대상 HTML 파일이 없습니다.")
        return
        
    print("\nPlaywright를 구동하여 이미지 캡처 작업을 시작합니다...")
    
    with sync_playwright() as p:
        # 브라우저 구동
        browser = p.chromium.launch()
        
        # 뷰포트 크기를 설정하고 device_scale_factor=2를 주어 고해상도로 캡처
        page = browser.new_page(
            viewport={"width": 760, "height": 1000},
            device_scale_factor=2
        )
        
        for branch, html_path in generated_files.items():
            img_filename = f"promo_{branch}.png"
            img_path = os.path.join(RESULT_DIR, img_filename)
            
            # 절대 경로 기반 로컬 URL 변환
            abs_url = f"file:///{os.path.abspath(html_path).replace(os.sep, '/')}"
            
            print(f"[{branch.upper()}] 캡처 중 -> {img_filename}")
            
            page.goto(abs_url)
            # 웹폰트 및 외부 이미지 렌더링을 위한 안전 대기시간 부여
            page.wait_for_timeout(1000)
            
            # full_page=True 옵션으로 720px 너비 컨테이너의 전체 높이에 맞추어 캡처
            page.screenshot(path=img_path, full_page=True)
            print(f"[{branch.upper()}] 캡처 완료: {img_path}")
            
        browser.close()
    print("[FINISHED] 모든 지점 홍보 이미지가 성공적으로 재생성되었습니다!")

if __name__ == "__main__":
    # 1단계: API 데이터 기반으로 HTML 생성
    html_files = build_templates()
    
    # 2단계: 생성된 HTML을 이미지로 캡처
    generate_images(html_files)
