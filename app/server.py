# -*- coding: utf-8 -*-
"""AI4En 应用入口：静态页面 + JSON 接口 + 文件导出。

启动：python server.py [--port 8848]
仅使用 Python 标准库，数据保存在 data/ai4en.db（首次启动自动写入演示数据）。
"""
from __future__ import annotations

import json
import mimetypes
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, unquote, urlparse

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from ai4en import api, auth, content, db, ppt_export, print_views, seed  # noqa: E402

WEB_DIR = os.path.join(APP_DIR, "web")
DEFAULT_PORT = 8848


def boot():
    db.init()
    created = seed.run()
    if created:
        log("已写入演示数据：6 名学生、2 个班级、Animals 课例与已发布任务。")
    log("模型配置：" + ("已配置 " + content.model_config()["model"] if content.model_config()["configured"]
                        else "未配置（生成时使用示例内容）"))


def log(message):
    print("[AI4En] " + message, flush=True)


class Handler(BaseHTTPRequestHandler):
    server_version = "AI4En/1.0"
    protocol_version = "HTTP/1.1"

    # ---------------------------------------------------------------- 基础
    def log_message(self, fmt, *args):  # 只保留错误级别的访问日志
        if str(args[1] if len(args) > 1 else "")[:1] in ("4", "5"):
            log("%s %s -> %s" % (self.command, self.path, args[1] if len(args) > 1 else ""))

    def _json(self, status, payload):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        for cookie in getattr(self, "_cookies", []):
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(raw)

    def _html(self, status, html):
        raw = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        for cookie in getattr(self, "_cookies", []):
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(raw)

    def _file(self, status, raw, filename, mime):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Content-Disposition",
                         "attachment; filename=\"%s\"; filename*=UTF-8''%s" % (filename.encode("ascii", "ignore").decode() or "export", quote(filename)))
        self.end_headers()
        self.wfile.write(raw)

    def _token(self):
        raw = self.headers.get("Cookie", "")
        for part in raw.split(";"):
            if "=" in part:
                key, value = part.strip().split("=", 1)
                if key == auth.SESSION_COOKIE:
                    return value
        return None

    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise api.ApiError(400, "请求内容不是合法的 JSON", "bad_json")

    # ---------------------------------------------------------------- 方法
    def do_GET(self):
        self.handle_any("GET")

    def do_POST(self):
        self.handle_any("POST")

    def do_PATCH(self):
        self.handle_any("PATCH")

    def do_DELETE(self):
        self.handle_any("DELETE")

    def handle_any(self, method):
        self._cookies = []
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        query = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        try:
            body = self._body() if method in ("POST", "PATCH") else {}
            token = self._token()
            user = auth.user_by_token(token)
            if path.startswith("/api/"):
                return self.handle_api(method, path, query, body, user, token)
            if path.startswith("/print/"):
                status, html = print_views.render(path, query, user)
                return self._html(status, html)
            return self.handle_static(method, path)
        except api.ApiError as exc:
            payload = {"error": exc.message, "code": exc.code}
            payload.update(exc.extra)
            return self._json(exc.status, payload)
        except BrokenPipeError:
            return None
        except Exception:  # noqa: BLE001
            log("未处理异常：" + traceback.format_exc())
            return self._json(500, {"error": "服务器内部错误，请稍后重试", "code": "internal"})

    def handle_api(self, method, path, query, body, user, token):
        if path == "/api/health":
            cfg = content.deepseek_config()
            return self._json(200, {"ok": True, "app": "AI4En", "db": os.path.basename(db.DB_PATH),
                                    "hasKey": cfg["configured"], "model": cfg["model"]})

        # 导出课件（二进制）
        if method == "GET" and path.startswith("/api/lessons/") and path.endswith("/export/pptx"):
            if not user or user["role"] != "teacher":
                raise api.ApiError(403, "只有教师可以导出课件", "forbidden")
            lesson_id = int(path.split("/")[3])
            lesson = api.load_lesson(lesson_id, user["id"])
            bundle = api.lesson_bundle(lesson)
            slides = (bundle["materials"].get("slides", {}).get("data") or [])
            raw = ppt_export.build({"title": lesson["title"], "grade": lesson["grade"]}, slides)
            name = lesson["title"].split(":")[0].strip() + "_课件.pptx"
            return self._file(200, raw, name,
                              "application/vnd.openxmlformats-officedocument.presentationml.presentation")

        ctx = {"user": user, "query": query, "body": body, "token": token, "method": method, "path": path}
        status, payload = api.dispatch(method, path, query, body, user, token)
        if path == "/api/login" and isinstance(payload, dict) and payload.get("token"):
            self._cookies.append(auth.SESSION_COOKIE + "=" + payload["token"] + "; Path=/; HttpOnly; SameSite=Lax; Max-Age=86400")
            payload.pop("token", None)
        if path == "/api/logout":
            self._cookies.append(auth.SESSION_COOKIE + "=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0")
        return self._json(status, payload)

    def handle_static(self, method, path):
        if method != "GET":
            raise api.ApiError(405, "静态资源只支持 GET 请求", "method_not_allowed")
        if path in ("/", "/index.html"):
            base = WEB_DIR
            target = os.path.join(WEB_DIR, "index.html")
        elif path.startswith("/static/"):
            base = os.path.join(WEB_DIR, "static")
            target = os.path.join(base, path[len("/static/"):])
        else:
            raise api.ApiError(404, "页面不存在", "not_found")
        target = os.path.normpath(target)
        base = os.path.normpath(base)
        if target != base and not target.startswith(base + os.sep):
            raise api.ApiError(404, "页面不存在", "not_found")
        if os.path.isdir(target):
            target = os.path.join(target, "index.html")
        if not os.path.isfile(target):
            raise api.ApiError(404, "页面不存在", "not_found")
        mime, _ = mimetypes.guess_type(target)
        with open(target, "rb") as fh:
            raw = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", (mime or "application/octet-stream") + ("; charset=utf-8" if mime and mime.startswith(("text", "application/javascript")) else ""))
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(raw)


def main():
    port = DEFAULT_PORT
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg in ("--port", "-p") and i + 1 < len(args):
            port = int(args[i + 1])
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    boot()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    log("服务已启动： http://127.0.0.1:%d/" % port)
    log("演示账号：t_wang / teach123（教师）· s_zhang / stu123（学生）· p_zhang / par123（家长）")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log("已停止")


if __name__ == "__main__":
    main()
