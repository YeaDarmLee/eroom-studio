import os
import json
import urllib.request
import urllib.error
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

import sys

# --- Logging Setup ---
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger('mule_crawler')
logger.setLevel(logging.INFO)
if not logger.handlers:
    log_path = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__)), 'mule_crawler.log')
    fh = RotatingFileHandler(log_path, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(fh)
    logger.addHandler(ch)

import builtins
def custom_print(*args, **kwargs):
    msg = " ".join(str(a) for a in args)
    if "[오류]" in msg or "Exception" in msg or "Error" in msg or "WARNING" in msg or "✖" in msg:
        logger.error(msg)
    else:
        logger.info(msg)
builtins.print = custom_print
# ---------------------

# .env 파일 로드 (PyInstaller 배포 환경을 고려한 절대 경로화)
if getattr(sys, 'frozen', False):
    BUNDLE_DIR = sys._MEIPASS
    USER_DIR = os.path.dirname(sys.executable)
else:
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
    USER_DIR = BUNDLE_DIR

env_path = os.path.join(USER_DIR, ".env")
load_dotenv(dotenv_path=env_path)

# 상수 정의
TEMPLATE_DIR = os.path.join(BUNDLE_DIR, "template")
HTML_OUT_DIR = os.path.join(BUNDLE_DIR, "result") # HTML은 임시 폴더에 저장 (상대경로 img 참조 위함)
RESULT_DIR = os.path.join(USER_DIR, "result")     # 최종 결과물은 사용자 폴더에 저장

if not os.path.exists(HTML_OUT_DIR):
    os.makedirs(HTML_OUT_DIR, exist_ok=True)
if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR, exist_ok=True)

API_BASE_URL = os.getenv("API_BASE_URL", "https://eroom-studio.co.kr")

# MULE_TARGET_BRANCHES 환경변수 로드 및 정제
target_branches_env = os.getenv("MULE_TARGET_BRANCHES")
if target_branches_env:
    BRANCHES = [b.strip().lower() for b in target_branches_env.split(",") if b.strip()]
else:
    BRANCHES = ["samsung", "hongdae", "incheon", "mokdong", "bongcheon", "bucheon"]


# 로컬 테스트 및 API 실패 시를 위한 Mock 데이터
MOCK_DATA = {
    "samsung": {
        "available_rooms": [
            {"floor": "3층", "name": "7호", "area": 5.75, "area_pyung": 5.75, "price": 500000, "description": "보컬 및 미디 작업 추천"},
            {"floor": "3층", "name": "14호", "area": 3.4, "area_pyung": 3.4, "price": 420000, "description": "보컬 및 미디 작업 추천"},
            {"floor": "3층", "name": "15호", "area": 3.4, "area_pyung": 3.4, "price": 420000, "description": "보컬 및 미디 작업 추천"},
            {"floor": "3층", "name": "16호", "area": 3.4, "area_pyung": 3.4, "price": 420000, "description": "보컬 및 미디 작업 추천"},
            {"floor": "3층", "name": "19호", "area": 5.95, "area_pyung": 5.95, "price": 550000, "description": "보컬 및 미디 작업 추천"}
        ],
        "is_fully_occupied": False,
        "next_available_date": None
    },
    "hongdae": {
        "available_rooms": [
            {"floor": "4층", "name": "403호", "area": 8.25, "area_pyung": 8.25, "price": 600000, "description": "보컬 및 미디 작업 추천"},
            {"floor": "4층", "name": "409호", "area": 8.25, "area_pyung": 8.25, "price": 600000, "description": "보컬 및 미디 작업 추천"}
        ],
        "is_fully_occupied": False,
        "next_available_date": None
    },
    "incheon": {
        "available_rooms": [
            {"floor": "4층", "name": "401호", "area": 7.26, "area_pyung": 7.26, "price": 450000, "description": "보컬, 미디, 개인 작업 권장"},
            {"floor": "4층", "name": "403호", "area": 8.25, "area_pyung": 8.25, "price": 500000, "description": "보컬 및 미디 작업 추천"}
        ],
        "is_fully_occupied": False,
        "next_available_date": None
    },
    "mokdong": {
        "available_rooms": [
            {"floor": "3층", "name": "316호", "area": 7.04, "area_pyung": 7.04, "price": 530000, "description": "보컬 및 미디 작업 추천"}
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
            {"floor": "5층", "name": "A", "area": 15, "area_pyung": 15, "price": 600000, "description": "보컬, 미디, 개인 악기 연습 권장 (A room)"},
            {"floor": "5층", "name": "B", "area": 15, "area_pyung": 15, "price": 800000, "description": "보컬, 미디, 개인 악기 연습 권장 (B room)"},
            {"floor": "5층", "name": "H", "area": 15, "area_pyung": 15, "price": 350000, "description": "보컬, 미디, 개인 악기 연습 권장 (H room)"}
        ],
        "is_fully_occupied": False,
        "next_available_date": None
    }
}

BRANCH_NAMES_KO = {"samsung": "삼성점", "hongdae": "홍대점", "incheon": "인천점", "mokdong": "목동점", "bongcheon": "봉천점", "bucheon": "부천점"}

def _http_get_json(url):
    """urllib 우선, SSL 등으로 실패하면 curl.exe(윈도우 인증서 저장소)로 재시도."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'EroomTemplateBuilder/1.0'})
        with urllib.request.urlopen(req, timeout=10.0) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"  urllib 실패 ({type(e).__name__}: {e}) -> curl로 재시도")
        import subprocess
        out = subprocess.run(["curl", "-s", "-f", "-m", "15", url], capture_output=True, timeout=20, check=True).stdout
        return json.loads(out.decode('utf-8'))

def fetch_branch_data(branch):
    """서버 API로부터 지점 정보를 가져옵니다. 실패 시 예외 (오래된 데이터 게시 방지)."""
    url = f"{API_BASE_URL}/api/public/branches/{branch}/rooms-status"
    print(f"[{branch.upper()}] API 호출 시도: {url}")
    data = None
    for attempt in range(2):
        try:
            data = _http_get_json(url)
            break
        except Exception as e:
            print(f"[{branch.upper()}] API 호출 실패 {attempt+1}/2 ({type(e).__name__}: {e})")
    if data is None:
        raise RuntimeError(f"[{branch.upper()}] API 조회 실패")
    print(f"[{branch.upper()}] API 연동 성공!")
    return data["data"] if "data" in data else data

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
        
        area_val = r.get('area', r.get('area_pyung', 0.0))
        if isinstance(area_val, (int, float)):
            area_str = f"{area_val:.2f}".rstrip('0').rstrip('.') if area_val % 1 != 0 else f"{int(area_val)}"
        else:
            area_str = str(area_val)
            
        cards.append(f"""
          <div
            style="background-color: #FAF8F5; border: 1px solid #EBE7E0; border-radius: 16px; padding: 22px 24px; display: flex; flex-direction: column; gap: 14px; box-shadow: 0 2px 8px rgba(42, 66, 58, 0.03); text-align: left;">
            <div style="display: flex; flex-direction: column; align-items: center; gap: 6px;">
              <span
                style="background-color: #EAE6DF; color: #5C554E; font-size: 15px; font-weight: 800; padding: 6px 0; border-radius: 8px; width: 100%; text-align: center; display: block;">{r['floor']} {r['name']}</span>
            </div>
            <div style="display: flex; flex-direction: column; gap: 8px; border-top: 1px solid #F3EFE9; border-bottom: 1px solid #F3EFE9; padding: 14px 0;">
              <div style="display: flex; align-items: center; font-size: 13.5px; color: #6E675F;">
                <span>면적: <strong style="color: #2A423A;">약 {area_str}㎡</strong></span>
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

def build_templates():
    """지점별 HTML 템플릿을 API 기반으로 변환하여 생성합니다."""
    generated_files = {}
    today_str = datetime.now().strftime("%y-%m-%d")
    
    source_path = os.path.join(TEMPLATE_DIR, "source_template.html")
    with open(source_path, 'r', encoding='utf-8') as f:
        template_content = f.read()

    for branch in BRANCHES:
        dest_path = os.path.join(HTML_OUT_DIR, f"template_{branch}.html")
        stale_img = os.path.join(RESULT_DIR, f"promo_{branch}.png")
        if os.path.exists(stale_img):
            os.remove(stale_img)  # 이전 이미지 잔존 방지

        try:
            rooms = fetch_branch_data(branch).get("available_rooms", [])
        except Exception as e:
            print(f"[ERROR] [{branch.upper()}] 데이터 조회 실패로 건너뜁니다: {e}")
            continue
        if not rooms:
            print(f"[{branch.upper()}] 빈방 없음 -> 건너뜁니다.")
            continue

        final_content = (template_content
            .replace("<!-- BRANCH_NAME -->", BRANCH_NAMES_KO.get(branch, branch))
            .replace("<!-- TODAY -->", today_str)
            .replace("<!-- ROOM_SECTION_PLACEHOLDER -->", generate_rooms_html(rooms)))

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
        # 로컬 구글 크롬 설치 경로 자동 탐색
        chrome_path = None
        import sys
        if sys.platform == "win32":
            username = os.environ.get("USERNAME", "")
            candidates = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                rf"C:\Users\{username}\AppData\Local\Google\Chrome\Application\chrome.exe"
            ]
            for c in candidates:
                if os.path.exists(c):
                    chrome_path = c
                    break
        elif sys.platform == "darwin":
            mac_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            if os.path.exists(mac_path):
                chrome_path = mac_path
        
        # 브라우저 구동 (로컬 크롬이 있으면 그것을 실행하여 내장 브라우저 바이너리 종속성 해소)
        if chrome_path:
            browser = p.chromium.launch(executable_path=chrome_path, headless=True)
        else:
            browser = p.chromium.launch(headless=True)
        
        # 뷰포트 크기를 설정하고 device_scale_factor=2를 주어 고해상도로 캡처
        page = browser.new_page(
            viewport={"width": 760, "height": 100},
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

def main():
    # 1단계: API 데이터 기반으로 HTML 생성
    html_files = build_templates()
    
    # 2단계: 생성된 HTML을 이미지로 캡처
    generate_images(html_files)

if __name__ == "__main__":
    main()
