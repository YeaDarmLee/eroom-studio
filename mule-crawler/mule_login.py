"""
뮬(mule.co.kr) 자동 로그인 크롤러
- 대시보드 형태의 인터랙티브 UI를 콘솔에 출력하여 진행 상황을 사용자 친화적으로 시각화합니다.
"""

import asyncio
import subprocess
import os
import sys
import time
import shutil
import urllib.request
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, BrowserContext

load_dotenv()

# 윈도우 환경에서 유니코드 특수문자 출력 시 UnicodeEncodeError 방지
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

MULE_URL = "https://www.mule.co.kr"
CDP_PORT = 9223
CDP_URL = f"http://127.0.0.1:{CDP_PORT}"


# ── 사용자의 실제 크롬 프로필 경로 ──
USERNAME = os.environ.get("USERNAME", "")
REAL_USER_DATA_DIR = rf"C:\Users\{USERNAME}\AppData\Local\Google\Chrome\User Data"
CHROME_PROFILE_DIR = os.getenv("CHROME_PROFILE_DIR", "Profile 1")
REAL_PROFILE_PATH = os.path.join(REAL_USER_DATA_DIR, CHROME_PROFILE_DIR)

from generate_templates_and_images import fetch_branch_data

# ── SEO 텍스트 생성용 한국어 지점 매핑 ──
BRANCH_NAMES_KO = {
    "samsung": "삼성점",
    "hongdae": "홍대점",
    "incheon": "인천점",
    "mokdong": "목동점",
    "bongcheon": "봉천점",
    "bucheon": "부천점"
}

def generate_seo_text(branch, data):
    branch_ko = BRANCH_NAMES_KO.get(branch.lower(), f"{branch.upper()}점")
    rooms = data.get("available_rooms", [])
    is_occupied = data.get("is_fully_occupied", False) or len(rooms) == 0
    next_date = data.get("next_available_date") or "2026-07-01"
    
    # 공실 목록 텍스트화
    if is_occupied:
        room_list_html = f"<li>현재 모든 룸이 만실 상태입니다. (가장 빠른 입실 가능 예정일: {next_date})</li>"
    else:
        room_list_html = ""
        for r in rooms:
            desc = r.get('description', '') or '쾌적한 연습 공간'
            desc = desc.replace('\n', ' • ').strip()
            room_list_html += f"<li>{r['floor']} {r['name']} (실평수: 약 {r['area_pyung']:.2f}평) - {desc}</li>"
            
    # 예약 및 문의 카드와 서비스 정보
    seo_html = f"""
<br><br>
<hr>
<h3>이룸스튜디오 {branch_ko} 실시간 공실 현황 & 서비스 안내</h3>
<br>
<p><strong>[실시간 이용 가능한 룸 정보]</strong></p>
<ul>
  {room_list_html}
</ul>
<br>
<p><strong>[이룸스튜디오 {branch_ko} 특별 할인 혜택]</strong></p>
<ul>
  <li><strong>6개월 계약 시</strong>: 특별 할인가 적용 혜택</li>
  <li><strong>12개월 계약 시</strong>: 추가 장기 계약 특별 할인 혜택</li>
  <li>※ 6개월/12개월 장기 계약 고객분들께 최대 혜택을 집중하여 제공해 드립니다.</li>
</ul>
<br>
<p><strong>[시설 및 프리미엄 서비스 안내]</strong></p>
<ul>
  <li>각 방 개별 디지털 도어락 완비로 철저한 프라이버시 보장</li>
  <li>완벽한 냉난방 시스템 (개별 에어컨 설치)</li>
  <li>초고속 기가 인터넷 및 Wi-Fi 제공으로 안정적인 미디 및 작업 환경 지원</li>
  <li>더 자세한 사진 및 정보는 공식 웹사이트에서 확인하실 수 있습니다.</li>
</ul>
<br>
<p><strong>[예약 & 문의 연락처]</strong></p>
<ul>
  <li>☎ 대표 전화번호: <strong>010-9488-5093</strong></li>
  <li>💬 카카오톡 ID: <strong>yhk5093</strong></li>
  <li>🌐 공식 홈페이지: <a href="https://eroom-studio.co.kr" target="_blank" rel="noopener">https://eroom-studio.co.kr</a></li>
</ul>
<p>24시간 언제든 편하게 문자나 카카오톡으로 지점명({branch_ko})과 함께 문의 남겨주시면 성심성의껏 답변해 드리겠습니다!</p>
<hr>
"""
    return seo_html.replace("\n", "").replace("'", "\\'")

# ── 복사될 크롤러 전용 임시 프로필 경로 ──
BOT_PROFILE_DIR = r"C:\workspace\Eroom-Studio\mule-crawler\chrome-debug-profile"

CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    rf"C:\Users\{USERNAME}\AppData\Local\Google\Chrome\Application\chrome.exe",
]

# ── 5대 주요 단계 정의 ──
stages = [
    {"desc": "이전 크롬 프로세스 정리 및 새 프로필 세션 데이터 복제", "status": "대기"},
    {"desc": "자동화 전용 크롬 브라우저 백그라운드 기동", "status": "대기"},
    {"desc": "브라우저 제어 모듈과 뮬(mule.co.kr) 페이지 연결", "status": "대기"},
    {"desc": "로그인 상태 확인 및 입력 폼 제어 (중복 로그인 시 로그아웃)", "status": "대기"},
    {"desc": "보안 검사(캡챠) 우회 대기 및 최종 로그인 승인", "status": "대기"}
]

notice_message = ""


def set_stage_status(index: int, status: str, error_msg: str = ""):
    """특정 단계의 상태를 업데이트하고 터미널에 로그를 남깁니다."""
    if 0 <= index < len(stages):
        stages[index]["status"] = status
        desc = stages[index]["desc"]
        err_suffix = f" ({error_msg})" if error_msg else ""
        print(f"[알림] {desc} -> {status}{err_suffix}")


def set_notice(msg: str):
    """안내 메시지를 일반 텍스트로 출력합니다."""
    print(f"  >>> {msg}")


def render_dashboard():
    """콘솔 대시보드 무시 (순차 텍스트 로그 출력 유지를 위해 비활성화)"""
    pass


def find_chrome() -> str | None:
    for p in CHROME_PATHS:
        if os.path.exists(p):
            return p
    return None


def copy_chrome_session() -> bool:
    """사용자의 실제 Chrome 프로필에서 로그인 정보 복사"""
    set_stage_status(0, "진행")
    os.makedirs(BOT_PROFILE_DIR, exist_ok=True)
    
    items_to_copy = [
        "Preferences",
        "Cookies",
        "Cookies-journal",
        "Network",
        "Local Storage",
    ]

    for item in items_to_copy:
        src = os.path.join(REAL_PROFILE_PATH, item)
        dst = os.path.join(BOT_PROFILE_DIR, item)
        
        if not os.path.exists(src):
            continue
            
        try:
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
        except Exception:
            pass

    set_stage_status(0, "완료")
    return True


def kill_existing_chrome() -> bool:
    """이전 실행된 봇 크롬 프로세스 정리"""
    try:
        if sys.platform == "win32":
            result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if f":{CDP_PORT}" in line and "LISTENING" in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        subprocess.run(["taskkill", "/f", "/pid", pid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        time.sleep(1)
        return True
    except Exception:
        return False


def launch_chrome() -> bool:
    """자동화 전용 크롬 기동"""
    set_stage_status(1, "진행")
    kill_existing_chrome()
    copy_chrome_session()

    chrome = find_chrome()
    if not chrome:
        set_stage_status(1, "오류", "컴퓨터에서 크롬 브라우저의 설치 주소를 감지하지 못했습니다.")
        return False

    subprocess.Popen([
        chrome,
        f"--remote-debugging-port={CDP_PORT}",
        f"--remote-debugging-address=127.0.0.1",
        f"--user-data-dir={BOT_PROFILE_DIR}",
        "--no-first-run",
        "--no-default-browser-check",
        MULE_URL,
    ])
    return True


def wait_for_chrome(timeout: int = 15) -> bool:
    """포트 통신 수립 대기"""
    urls = [CDP_URL, f"http://127.0.0.1:{CDP_PORT}"]
    for _ in range(timeout):
        for url in urls:
            try:
                urllib.request.urlopen(f"{url}/json/version", timeout=1)
                set_stage_status(1, "완료")
                return True
            except Exception:
                pass
        time.sleep(1)
    set_stage_status(1, "오류", "크롬 브라우저 실행 시간을 초과했습니다. 다시 가동해 주세요.")
    return False


async def get_mule_page(playwright) -> tuple[object, BrowserContext, Page]:
    """브라우저 권한 연결"""
    set_stage_status(2, "진행")
    try:
        browser = await playwright.chromium.connect_over_cdp(CDP_URL)
    except Exception as e:
        set_stage_status(2, "오류", f"브라우저 인터페이스 연동 실패: {e}")
        raise

    context = browser.contexts[0] if browser.contexts else await browser.new_context()

    mule_page = None
    for p in context.pages:
        if "mule.co.kr" in p.url:
            mule_page = p
            await mule_page.bring_to_front()
            break

    if not mule_page:
        mule_page = await context.new_page()
        await mule_page.goto(MULE_URL, wait_until="domcontentloaded")
        await mule_page.wait_for_timeout(2000)

    # 로그아웃 확인 창 등 다이얼로그 발생 시 자동 확인 처리 (1회만 등록)
    mule_page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))

    set_stage_status(2, "완료")
    return browser, context, mule_page


async def do_login(page: Page, mule_id: str, mule_pw: str, branch_name: str) -> bool:
    """로그인 폼 및 상태 조율"""
    set_stage_status(3, "진행")
    
    if not mule_id or not mule_pw:
        set_stage_status(3, "오류", f"[{branch_name.upper()}] .env 파일에 로그인 설정이 존재하지 않습니다.")
        return False

    await page.wait_for_timeout(2000)

    # 로그인 상태 분석
    is_logged_in = await page.evaluate("""
        () => {
            const logoutBtn = document.querySelector('li.l-logout');
            if (!logoutBtn) return false;
            const style = window.getComputedStyle(logoutBtn);
            return style.display !== 'none' && style.visibility !== 'hidden';
        }
    """)

    if is_logged_in:
        set_notice(f"[{branch_name.upper()}] 이전 로그인 계정이 감지되었습니다. 전환을 위해 로그아웃 중...")
        try:
            await page.evaluate("document.querySelector('li.l-logout').click()")
            await page.wait_for_timeout(3000)
            await page.goto(MULE_URL, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
        except Exception as e:
            pass

    # 로그인 레이어 열기
    try:
        await page.evaluate("document.querySelector('li.l-login').click()")
        await page.wait_for_timeout(1500)
    except Exception as e:
        set_stage_status(3, "오류", f"[{branch_name.upper()}] 로그인 창 활성화 중 문제가 생겼습니다.")
        return False

    set_notice(f"[{branch_name.upper()}] 로그인 양식 입력 완료 (입력 ID: {mule_id})")
    try:
        id_input = page.locator("#login-user-id")
        await id_input.wait_for(state="visible", timeout=5000)
        await id_input.fill(mule_id)

        pw_input = page.locator("#login-user-pw")
        await pw_input.wait_for(state="visible", timeout=5000)
        await pw_input.fill(mule_pw)
    except Exception as e:
        set_stage_status(3, "오류", f"[{branch_name.upper()}] 로그인 데이터를 입력 칸에 넣는 데 실패했습니다.")
        return False

    set_stage_status(3, "완료")
    
    # 5단계 시작
    set_stage_status(4, "진행")
    set_notice(f"[{branch_name.upper()}] Cloudflare Turnstile 보안 검사 해결을 기다립니다 (4초 대기)...")

    # 캡챠 클릭 시도
    try:
        turnstile = page.frame_locator("iframe[src*='challenges.cloudflare.com']")
        checkbox = turnstile.locator("[type='checkbox'], .ctp-checkbox-label, input")
        if await checkbox.count() > 0:
            await checkbox.first.click(timeout=3000)
            set_notice(f"[{branch_name.upper()}] 보안 확인 클릭 완료. 계속해서 우회 검사를 확인합니다.")
    except Exception:
        pass
    
    await page.wait_for_timeout(4000)

    set_notice(f"[{branch_name.upper()}] 로그인 제출 요청을 브라우저에 전달했습니다.")
    await page.evaluate("document.querySelector('a.login-bt.login').click()")
    await page.wait_for_timeout(4000)

    # 성공 체크
    success = await page.evaluate("""
        () => {
            const loginBtn = document.querySelector('li.l-login');
            if (!loginBtn) return true;
            const style = window.getComputedStyle(loginBtn);
            return style.display === 'none' || style.visibility === 'hidden';
        }
    """)

    if success:
        set_stage_status(4, "완료", f"[{branch_name.upper()}] 뮬(mule.co.kr) 사이트 로그인이 성공적으로 끝났습니다.")
        return True
    else:
        set_stage_status(4, "오류")
        set_notice(f"[{branch_name.upper()}] 보안 확인을 바로 통과하지 못했습니다. 크롬 창을 보시고 캡챠를 눌러서 직접 로그인을 완료해 주십시오.")
        print(f"  👉 수동 로그인을 마친 뒤, 이 창에서 [Enter] 키를 누르면 다음 작업을 속개합니다...")
        await asyncio.get_event_loop().run_in_executor(None, input)

        await page.goto(MULE_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        success = await page.evaluate("""
            () => {
                const loginBtn = document.querySelector('li.l-login');
                if (!loginBtn) return true;
                const style = window.getComputedStyle(loginBtn);
                return style.display === 'none' || style.visibility === 'hidden';
            }
        """)
        if success:
            set_stage_status(4, "완료", f"[{branch_name.upper()}] 수동 로그인 성공이 식별되었습니다.")
        else:
            set_notice(f"[{branch_name.upper()}] 로그인을 감지하지 못했습니다.")
        return success


async def main():
    # 1단계: 실시간 템플릿 및 이미지 자동 생성
    print("=" * 70)
    print(" [1단계] 실시간 지점 공실 템플릿 및 홍보 이미지 자동 생성")
    print("=" * 70)
    try:
        # 비동기 Playwright 프로세스 공간 충돌을 방지하기 위해 서브프로세스로 안전하게 가동
        # capture_output을 사용하지 않고 부모 프로세스의 stdout/stderr를 공유하여 터미널에 실시간으로 로그가 표시됩니다.
        import sys
        result = subprocess.run([sys.executable, "generate_templates_and_images.py"])
        if result.returncode != 0:
            print(f"\n✖ 에셋 생성 스크립트가 비정상 종료되었습니다 (종료 코드: {result.returncode})\n")
        else:
            print("\n✔ 모든 홍보용 이미지 애셋 빌드 완료!\n")
    except Exception as e:
        print(f"✖ 에셋 생성 중 예외 발생: {e}\n")

    print("=" * 70)
    print(" [2단계] 자동화용 크롬 브라우저 기동 및 원격 포트 연결")
    print("=" * 70)
    
    chrome_running = False
    try:
        urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=2)
        chrome_running = True
        print("[정보] 이미 실행되어 있는 자동화용 브라우저 세션을 재활용합니다.")
    except Exception:
        pass

    if not chrome_running:
        ok = launch_chrome()
        if not ok:
            print("[오류] 크롬 브라우저 가동에 실패했습니다.")
            sys.exit(1)
        # 크롬 프로세스 안정화를 위해 3초 대기 후 소켓 통신 연결 대기 진입
        time.sleep(3)
        if not wait_for_chrome(timeout=15):
            print("[오류] 크롬 디버깅 포트(9223) 연결에 실패했습니다.")
            sys.exit(1)

    BRANCHES = ["samsung", "hongdae", "incheon", "mokdong", "bongcheon", "bucheon"]

    print("\n" + "=" * 70)
    print(" [3단계] 뮬(mule.co.kr) 지점별 순환 로그인 시작")
    print("=" * 70)

    playwright = await async_playwright().start()
    try:
        browser, context, page = await get_mule_page(playwright)

        for idx, branch in enumerate(BRANCHES):
            # [힐링 로직] 만약 이전 지점 작업 도중 탭이 크래시 나거나 닫혔을 경우, 새 탭 생성하여 복구
            try:
                if page.is_closed():
                    raise Exception("Page is closed")
            except Exception:
                print("[정보] 이전 작업 중 브라우저 페이지가 닫혔거나 크래시가 감지되어 새 탭으로 복구합니다.")
                try:
                    page = await context.new_page()
                    await page.goto(MULE_URL, wait_until="domcontentloaded")
                    await page.wait_for_timeout(2000)
                except Exception as ne:
                    print(f"[오류] 새 탭 생성 복구에 실패했습니다 (계속 진행 시도): {ne}")

            print(f"\n--- [{idx+1}/6] {branch.upper()} 지점 로그인 처리 ---")
            
            branch_id = os.getenv(f"MULE_ID_{branch.upper()}")
            branch_pw = os.getenv(f"MULE_PW_{branch.upper()}")
            
            if not branch_id or not branch_pw:
                print(f"[경고] [{branch.upper()}] 계정 정보(MULE_ID_{branch.upper()})가 .env에 존재하지 않아 건너뜁니다.")
                await asyncio.sleep(1)
                continue
                
            success = await do_login(page, branch_id, branch_pw, branch)
            
            if success:
                print(f"✔ [{branch.upper()}] 계정({branch_id}) 로그인 완료! 리다이렉트 안정을 위해 3초간 대기합니다...")
                await page.wait_for_timeout(3000)
                
                print(f"  >>> 홍보글 작성/확인 페이지로 이동합니다...")
                try:
                    # wait_until="commit"을 사용하여 무거운 리소스(광고/이미지) 대기 중 크래시 가능성 원천 방지
                    await page.goto("https://www.mule.co.kr/bbs/info/room?v=w&", wait_until="commit", timeout=12000)
                    
                    # 폼 자동 기입 프로세스 시작
                    print(f"  >>> [{branch.upper()}] 폼 데이터 자동 입력 중...")
                    # 1. 구분 선택
                    await page.wait_for_selector("select#input-category", timeout=5000)
                    await page.select_option("select#input-category", "개인연습실")
                    
                    # 2. 옵션 선택 (주차, 24시, 숙식)
                    for val in ["주차", "24시", "숙식"]:
                        checkbox = page.locator(f"input[type='checkbox'][value='{val}']")
                        if await checkbox.is_visible():
                            if not await checkbox.is_checked():
                                await checkbox.check()
                                
                    # 3. 홈페이지 주소 기입
                    homepage_input = page.locator("input[v-model='bbs.homepage']").first
                    if not await homepage_input.is_visible():
                        homepage_input = page.locator("input[placeholder*='http://']").first
                    await homepage_input.fill("https://eroom-studio.co.kr")
                    
                    # 4. 전화번호 기입
                    await page.fill("input#input-sell-tel", "01094885093")
                    
                    # 5. 제목 기입 (SEO 및 클릭률 극대화 하이브리드 제목 - .env에서 관리)
                    branch_upper = branch.upper()
                    title_text = os.getenv(
                        f"MULE_TITLE_{branch_upper}",
                        f"이룸스튜디오 {branch_upper}점"  # .env에 없을 경우 기본값
                    )
                    await page.fill("input#input-title", title_text)
                    
                    # 6. 주소 검색 및 상세주소 기입
                    addr_map = {
                        "samsung": ("서울특별시 강남구 삼성동 151-29 이호빌딩", "3층"),
                        "hongdae": ("서울특별시 마포구 서교동 352-31", "3층"),
                        "incheon": ("인천광역시 남동구 간석동 117-18", "4층"),
                        "mokdong": ("서울특별시 양천구 신정동 902-4", "3층 4층"),
                        "bongcheon": ("서울특별시 관악구 봉천동 931-11", "2층 3층"),
                        "bucheon": ("경기도 부천시 상동 407-2 반달빌딩", "5층, H-Ground")
                    }
                    addr_info = addr_map.get(branch.lower())
                    if addr_info:
                        search_addr, detail_addr = addr_info
                        try:
                            # 6-1. '주소검색' 버튼 클릭하여 검색 모드로 전환
                            juso_btn = page.locator("div.juso-btn a").filter(has_text="주소검색").first
                            await juso_btn.wait_for(state="visible", timeout=4000)
                            await juso_btn.click()
                            
                            # 6-2. 주소 검색창 입력
                            await page.wait_for_selector("input#search-map-text", timeout=4000)
                            await page.fill("input#search-map-text", search_addr)
                            
                            # 6-3. 검색 버튼 클릭
                            search_btn = page.locator("div.juso-btn a").filter(has_text="검색").first
                            await search_btn.click()
                            
                            # 6-4. 결과 리스트 대기 및 클릭
                            await page.wait_for_selector("a.pointer", timeout=4000)
                            await page.locator("a.pointer").first.click()
                            
                            # 6-5. 상세주소 입력창 대기 및 입력
                            await page.wait_for_selector("input[placeholder*='상세주소']", timeout=4000)
                            await page.fill("input[placeholder*='상세주소']", detail_addr)
                            
                            print(f"  >>> [{branch.upper()}] 주소 설정 완료: {search_addr} / {detail_addr}")
                        except Exception as ae:
                            print(f"  >>> [{branch.upper()}] 주소 자동 기입 중 문제 발생: {ae}")
                    
                    # 7. 본문 이미지 등록 (Summernote)
                    try:
                        print(f"  >>> [{branch.upper()}] 본문 에디터 홍보 이미지 업로드 진행 중...")
                        # 7-1. 에디터의 '사진등록' 아이콘 클릭
                        await page.locator("i.note-icon-picture").first.click()
                        
                        # 7-2. 이미지 파일 경로 지정 및 업로드
                        promo_image_path = os.path.abspath(f"result/promo_{branch.lower()}.png")
                        if os.path.exists(promo_image_path):
                            file_input = page.locator("input.note-image-input[type='file']").first
                            await file_input.wait_for(state="attached", timeout=4000)
                            await file_input.set_input_files(promo_image_path)
                            
                            # 7-3. '그림 삽입' 버튼이 존재하고 활성화되었는지 판단하여 클릭
                            await page.wait_for_timeout(1500)  # 파일 선택 후 모달 처리 대기
                            insert_btn = page.locator("input.note-image-btn").first
                            if await insert_btn.is_visible() and not await insert_btn.is_disabled():
                                await insert_btn.click()
                                print(f"  >>> [{branch.upper()}] '그림 삽입' 버튼 클릭 완료")
                            print(f"  >>> [{branch.upper()}] 홍보 이미지 등록 완료!")
                            
                            # 7-4. 본문 하단에 SEO 최적화용 텍스트 추가 주입 (Summernote API)
                            try:
                                branch_data = fetch_branch_data(branch)
                                seo_html = generate_seo_text(branch, branch_data)
                                
                                await page.evaluate(f"""() => {{
                                    const currentCode = $('#summernote').summernote('code');
                                    $('#summernote').summernote('code', currentCode + '{seo_html}');
                                }}""")
                                print(f"  >>> [{branch.upper()}] 본문 에디터에 SEO 텍스트 추가 기입 완료!")
                            except Exception as se:
                                print(f"  >>> [{branch.upper()}] SEO 텍스트 추가 중 문제 발생: {se}")
                        else:
                            print(f"  >>> [경고] [{branch.upper()}] 홍보용 이미지 파일이 경로에 존재하지 않습니다: {promo_image_path}")
                    except Exception as ie:
                        print(f"  >>> [{branch.upper()}] 이미지 자동 업로드 중 예외 발생: {ie}")
                    
                    # 8. 이미지 렌더링 대기 (에디터 내 이미지 로딩 완료 후 진행)
                    print(f"  >>> [{branch.upper()}] 이미지 렌더링 대기 중... (5초)")
                    await page.wait_for_timeout(5000)
                    
                    # 9. 이용약관 동의 체크박스 클릭
                    try:
                        agree_checkbox = page.locator("div.checker-label").first
                        await agree_checkbox.wait_for(state="visible", timeout=4000)
                        await agree_checkbox.click()
                        print(f"  >>> [{branch.upper()}] 이용약관 동의 체크박스 클릭 완료!")
                    except Exception as ae:
                        print(f"  >>> [{branch.upper()}] 이용약관 동의 클릭 중 문제 발생: {ae}")
                    
                    # 10. 저장 버튼 클릭
                    try:
                        save_btn = page.locator("a#bt-save")
                        await save_btn.wait_for(state="visible", timeout=4000)
                        await save_btn.click()
                        print(f"  >>> [{branch.upper()}] 저장 버튼 클릭 완료! 게시글 등록 요청 전송!")
                        await page.wait_for_timeout(2000)  # 저장 처리 대기
                    except Exception as se:
                        print(f"  >>> [{branch.upper()}] 저장 버튼 클릭 중 문제 발생: {se}")
                    
                    print(f"  >>> [{branch.upper()}] 모든 홍보 필수 항목 및 이미지 자동 입력 완료!")
                    print(f"  >>> 저장 완료. 5초 대기 후 다음 계정 전환...")
                except Exception as ge:
                    print(f"  >>> 페이지 이동 및 기입 중 예외 발생: {ge}")
                await asyncio.sleep(5)
            else:
                print(f"✖ [{branch.upper()}] 계정({branch_id}) 로그인 실패! 3초 대기 후 전환...")
                await asyncio.sleep(3)

        print("\n" + "=" * 70)
        print(" [4단계] 모든 작업 완료 및 크롬 브라우저 연결 종료")
        print("=" * 70)
        await asyncio.sleep(3)

    finally:
        await playwright.stop()
        print("[완료] Playwright 엔진을 종료하고 브라우저 핸들을 반환하였습니다.")


if __name__ == "__main__":
    asyncio.run(main())
