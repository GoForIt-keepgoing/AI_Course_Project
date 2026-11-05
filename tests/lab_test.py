# -*- coding: utf-8 -*-
"""助教完整版（/static/lab/）的入口检查。

用法：python tests/lab_test.py [base_url]
默认 http://127.0.0.1:8848。只做只读检查；未配置 Key 时验证 /api/chat 返回 503。
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8848").rstrip("/")
RESULTS = []


def check(name, ok, actual):
    RESULTS.append(ok)
    print(("  PASS  " if ok else "  FAIL  ") + name + " ｜实际：" + actual, flush=True)


def get(path, raw=False):
    with urllib.request.urlopen(BASE + path, timeout=10) as resp:
        body = resp.read()
        return resp.status, (body if raw else json.loads(body.decode("utf-8")))


def post(path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode("utf-8"))
        except Exception:
            return exc.code, {}


def main():
    status, raw = get("/static/lab/", raw=True)
    html = raw.decode("utf-8", "ignore")
    check("完整版入口可打开", status == 200 and "小学英语 AI 助教" in html, "HTTP %s" % status)

    status, raw = get("/static/lab/app.js", raw=True)
    check("完整版脚本可加载", status == 200 and len(raw) > 50000, "HTTP %s / %s bytes" % (status, len(raw)))

    status, data = get("/api/health")
    check("健康检查带 hasKey", status == 200 and "hasKey" in data, "hasKey=%s" % data.get("hasKey"))

    status, data = post("/api/chat", {"message": "Hello", "mode": "scene", "scene": "restaurant"})
    if data.get("reply"):
        check("模型代理可用（已配置 Key）", status == 200, "HTTP %s / 已返回回复" % status)
    else:
        check("未配置 Key 时明确返回 503", status == 503 and data.get("code") == "no_key",
              "HTTP %s / %s" % (status, data.get("code")))

    passed = sum(1 for x in RESULTS if x)
    print("\n合计 %s 项，通过 %s 项" % (len(RESULTS), passed), flush=True)
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
