from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8000
BIND = "0.0.0.0"          # ⚠️ 127.0.0.1로 두면 밖에서 절대 안 붙는다
BODY = "<h1>배포됐습니다 🎉</h1>"


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(BODY.encode())


# ⚠️ 이 줄이 없으면 테스트가 app.py를 읽는 순간 서버가 켜져서 영영 안 끝납니다.
if __name__ == "__main__":
    HTTPServer((BIND, PORT), H).serve_forever()
