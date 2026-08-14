"""AI 프로필 사진관 — 10주 개발 클래스 배포 실습용 데모.

⭐ 이 앱에는 **진짜 AI가 없다. 그게 요점이다.**
   만들기 전에 먼저 올려서, 사람들이 신청을 하는지부터 본다.
   (수업에서 본 AI 인물사진 앱도 똑같이 "되는 것처럼" 만들어 올린 것이었다.)

설치할 것 없음 — 파이썬만 있으면 돈다.
"""
import os
import smtplib
import ssl
import threading
from email.message import EmailMessage
from http.server import HTTPServer, SimpleHTTPRequestHandler
from json import dumps
from pathlib import Path
from urllib.parse import parse_qs

PORT = 8000
BIND = "0.0.0.0"          # ⚠️ 127.0.0.1로 두면 밖에서 절대 안 붙는다

HERE = Path(__file__).parent
WAITLIST = HERE / "waitlist.txt"     # 신청이 쌓이는 곳. 앱을 갈아끼워도 이건 남는다
HEADLINE = "나를 닮은 AI 프로필"       # ← test_app.py가 보는 딱 한 마디

# ─────────────────────────────────────────────────────────────────────
# 신청 알림 메일 — 안 해도 앱은 그대로 돕니다 (설정한 사람만 메일이 옵니다).
#
# ⚠️ 여기에 주소·비밀번호를 **직접 적지 마세요.** 이 코드는 GitHub에 올라가고,
#    올라간 순간 전 세계가 봅니다. 그래서 값은 코드 밖(= 환경변수)에 둡니다.
#    수업에서 말한 "현관에 붙여둔 열쇠"가 바로 이 얘기예요.
#
#   맥·리눅스 :  MAIL_TO=나@gmail.com MAIL_FROM=나@gmail.com \
#                MAIL_APP_PASSWORD=앱비밀번호16자리 python3 app.py
#   윈도우    :  $env:MAIL_TO="나@gmail.com"; $env:MAIL_FROM="나@gmail.com"
#                $env:MAIL_APP_PASSWORD="앱비밀번호16자리"; python3 app.py
#
#   앱 비밀번호 = Google 계정 → 보안 → 2단계 인증 → 앱 비밀번호 (16자리).
#   평소 쓰는 Gmail 비밀번호로는 안 됩니다.
# ─────────────────────────────────────────────────────────────────────
MAIL_TO = os.environ.get("MAIL_TO", "").strip()
MAIL_FROM = os.environ.get("MAIL_FROM", "").strip()
# 구글이 앱 비밀번호를 "abcd efgh ijkl mnop" 처럼 4자씩 띄어서 보여준다 → 띄어쓰기는 빼고 쓴다
MAIL_APP_PASSWORD = os.environ.get("MAIL_APP_PASSWORD", "").replace(" ", "")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def mail_enabled() -> bool:
    return bool(MAIL_TO and MAIL_FROM and MAIL_APP_PASSWORD)


def send_mail(name: str, total: int) -> None:
    """신청 한 건을 메일로 알린다. 실패해도 앱은 계속 돈다."""
    msg = EmailMessage()
    msg["Subject"] = f"[AI 프로필 사진관] 새 신청 — {name}"
    msg["From"] = MAIL_FROM
    msg["To"] = MAIL_TO
    msg.set_content(
        f"새로운 신청이 들어왔습니다.\n\n"
        f"  이름   : {name}\n"
        f"  누적   : {total}명\n\n"
        f"— 10주 개발 클래스 배포 실습 데모에서 자동 발송"
    )
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as s:
            s.starttls(context=ssl.create_default_context())
            s.login(MAIL_FROM, MAIL_APP_PASSWORD)
            s.send_message(msg)
        print(f"[메일] {MAIL_TO} 로 발송 완료 ({name})")
    except Exception as e:                      # 메일이 안 가도 신청은 이미 저장됐다
        print(f"[메일] 발송 실패 — {e}")


def waitlist_count() -> int:
    """지금까지 몇 명이 신청했나."""
    if not WAITLIST.exists():
        return 0
    return len([x for x in WAITLIST.read_text(encoding="utf-8").splitlines() if x.strip()])


def add_to_waitlist(name: str) -> int:
    with WAITLIST.open("a", encoding="utf-8") as f:
        f.write(name.strip().replace("\n", " ")[:40] + "\n")
    return waitlist_count()


def page() -> str:
    """index.html을 읽어서 신청자 수만 채운다."""
    html = (HERE / "index.html").read_text(encoding="utf-8")
    return html.replace("{{count}}", str(waitlist_count()))


# 사진(img/…)처럼 그냥 내려주기만 하면 되는 파일은 파이썬이 대신 처리해 준다.
PRIVATE = {"/waitlist.txt", "/app.py"}     # 밖에서 못 보게 막을 것


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(HERE), **kw)

    def _send(self, body: str, ctype: str = "text/html; charset=utf-8") -> None:
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(page())                  # 첫 화면은 신청자 수를 채워서
        elif self.path in PRIVATE:
            self.send_error(404)                # 신청자 명단은 아무나 못 본다
        else:
            super().do_GET()                    # img/… 같은 파일은 그대로

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        form = parse_qs(self.rfile.read(length).decode("utf-8"))
        name = (form.get("name") or [""])[0].strip() or "이름 없음"
        total = add_to_waitlist(name)

        # 메일은 3~5초 걸릴 수 있다 → 따로 보내고 화면은 바로 넘긴다
        if mail_enabled():
            threading.Thread(target=send_mail, args=(name, total), daemon=True).start()

        self._send(dumps({"count": total, "mailed": mail_enabled()}),
                   "application/json; charset=utf-8")

    def log_message(self, fmt, *args):      # 터미널을 조용하게
        pass


# ⚠️ 이 줄이 없으면 테스트가 app.py를 읽는 순간 서버가 켜져서 영영 안 끝난다
if __name__ == "__main__":
    print(f"→ http://localhost:{PORT} 에서 열립니다 (끄려면 Ctrl+C)")
    print(f"  신청 알림 메일: {'켜짐 → ' + MAIL_TO if mail_enabled() else '꺼짐 (환경변수 미설정)'}")
    HTTPServer((BIND, PORT), H).serve_forever()
