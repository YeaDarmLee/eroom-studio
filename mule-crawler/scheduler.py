"""6시간마다 mule_login.py 실행. 마지막 성공 시각을 last_run.json에 저장 -> 재부팅/종료 후에도 경과 시간 계산."""
import json, os, socket, subprocess, sys, time
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "last_run.json")
LOG = os.path.join(BASE, "scheduler.log")
INTERVAL = timedelta(hours=6)
RETRY = timedelta(minutes=30)  # 실패 시 재시도 간격
CHECK_SEC = 60


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


def load():
    try:
        with open(STATE, encoding="utf-8") as f:
            d = json.load(f)
        return {k: datetime.fromisoformat(v) for k, v in d.items()}
    except Exception:
        return {}


def save(d):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump({k: v.isoformat() for k, v in d.items()}, f)


def main():
    # 중복 실행 방지 (같은 포트 점유 시 종료)
    lock = socket.socket()
    try:
        lock.bind(("127.0.0.1", 47123))
    except OSError:
        sys.exit("이미 scheduler가 실행 중입니다.")

    log("scheduler 시작")
    while True:
        st = load()
        now = datetime.now()
        due = now - st.get("success", datetime.min) >= INTERVAL
        cooled = now - st.get("attempt", datetime.min) >= RETRY
        if due and cooled:
            log(f"실행 시작 (마지막 성공: {st.get('success', '없음')})")
            st["attempt"] = now
            save(st)
            env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
            rc = subprocess.run([sys.executable, "mule_login.py"], cwd=BASE, env=env,
                                stdin=subprocess.DEVNULL).returncode
            if rc == 0:
                st["success"] = datetime.now()
                save(st)
            log(f"실행 종료 rc={rc}" + ("" if rc == 0 else f" -> {RETRY} 후 재시도"))
        time.sleep(CHECK_SEC)


if __name__ == "__main__":
    main()
