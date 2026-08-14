"""AI 프로필 사진관 — 10주 개발 클래스 배포 실습용 데모.

⭐ 이 앱에는 **진짜 AI가 없다. 그게 요점이다.**
   만들기 전에 먼저 올려서, 사람들이 신청을 하는지부터 본다.
   (수업에서 본 AI 인물사진 앱도 똑같이 "되는 것처럼" 만들어 올린 것이었다.)

설치할 것 없음 — 파이썬만 있으면 돈다.
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs

PORT = 8000
BIND = "0.0.0.0"          # ⚠️ 127.0.0.1로 두면 밖에서 절대 안 붙는다

HERE = Path(__file__).parent
WAITLIST = HERE / "waitlist.txt"     # 신청이 쌓이는 곳. 앱을 갈아끼워도 이건 남는다
HEADLINE = "나를 닮은 AI 프로필"       # ← test_app.py가 보는 딱 한 마디

DONE_BANNER = """
  <div class="done">
    <div class="pop">🎉</div>
    <h2>신청이 접수됐어요!</h2>
    <p class="badge">⏳ 대기자 명단에 등록되었습니다</p>
    <p class="fine">신청이 많아 순서대로 연락드리고 있어요. 자리가 나면 알려드릴게요.</p>
  </div>
"""


def waitlist_count() -> int:
    """지금까지 몇 명이 신청했나."""
    if not WAITLIST.exists():
        return 0
    return len([x for x in WAITLIST.read_text(encoding="utf-8").splitlines() if x.strip()])


def add_to_waitlist(name: str) -> None:
    with WAITLIST.open("a", encoding="utf-8") as f:
        f.write(name.strip().replace("\n", " ")[:40] + "\n")


def page(done: bool = False) -> str:
    """index.html을 읽어서 빈칸 두 개를 채운다."""
    html = (HERE / "index.html").read_text(encoding="utf-8")
    return (html
            .replace("{{count}}", str(waitlist_count()))
            .replace("{{done}}", DONE_BANNER if done else ""))


# 사진(img/…)처럼 그냥 내려주기만 하면 되는 파일은 파이썬이 대신 처리해 준다.
PRIVATE = {"/waitlist.txt", "/app.py"}     # 밖에서 못 보게 막을 것


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(HERE), **kw)

    def _send(self, html: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(page())                  # 첫 화면은 빈칸을 채워서
        elif self.path in PRIVATE:
            self.send_error(404)                # 신청자 명단은 아무나 못 본다
        else:
            super().do_GET()                    # img/… 같은 파일은 그대로

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        form = parse_qs(self.rfile.read(length).decode("utf-8"))
        name = (form.get("name") or [""])[0]
        if name.strip():
            add_to_waitlist(name)
        self._send(page(done=True))

    def log_message(self, fmt, *args):      # 터미널을 조용하게
        pass


# ⚠️ 이 줄이 없으면 테스트가 app.py를 읽는 순간 서버가 켜져서 영영 안 끝난다
if __name__ == "__main__":
    print(f"→ http://localhost:{PORT} 에서 열립니다 (끄려면 Ctrl+C)")
    HTTPServer((BIND, PORT), H).serve_forever()
