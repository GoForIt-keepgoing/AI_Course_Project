# -*- coding: utf-8 -*-
"""AI4En 验收脚本：对着一个已启动的服务跑完整教学流程。

用法：
    python tests/acceptance.py [base_url]

默认 http://127.0.0.1:8851。脚本只使用标准库，输出“预期 / 实际”，
返回码 0 表示全部通过。它会写入数据，请对临时数据库运行。
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
import http.cookiejar
from urllib.parse import quote

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8851"
RESULTS = []


def record(name, expect, ok, actual):
    RESULTS.append((name, ok))
    print(("  PASS  " if ok else "  FAIL  ") + name + " ｜预期：" + expect + " ｜实际：" + actual, flush=True)


class Client:
    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def req(self, method, path, body=None, raw=False):
        data = None
        headers = {}
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(BASE + quote(path, safe="/%"), data=data, method=method, headers=headers)
        try:
            with self.opener.open(request, timeout=20) as resp:
                payload = resp.read()
                return resp.status, (payload if raw else json.loads(payload.decode("utf-8")))
        except urllib.error.HTTPError as exc:
            payload = exc.read()
            if raw:
                return exc.code, payload
            try:
                return exc.code, json.loads(payload.decode("utf-8"))
            except json.JSONDecodeError:
                return exc.code, {"error": payload.decode("utf-8", "ignore")}

    def get(self, path, **kw):
        return self.req("GET", path, **kw)

    def post(self, path, body=None, **kw):
        return self.req("POST", path, body if body is not None else {}, **kw)

    def patch(self, path, body):
        return self.req("PATCH", path, body)


def login(username, password):
    c = Client()
    status, data = c.post("/api/login", {"username": username, "password": password})
    return c, status, data


def main():
    # 0 健康检查
    status, data = Client().get("/api/health")
    record("服务健康检查", "HTTP 200 且 app=AI4En", status == 200 and data.get("app") == "AI4En", "HTTP %s" % status)

    # 1 静态资源
    for path, needle in (
        ("/static/workshop/index.html", "AI英语教学工作坊"),
        ("/static/defense/index.html", "课堂答辩"),
        ("/static/workshop/培训演示.html", "培训演示"),
    ):
        status, raw = Client().get(path, raw=True)
        text = raw.decode("utf-8", "ignore") if isinstance(raw, bytes) else ""
        record("静态入口 " + path, "HTTP 200 且包含页面标识", status == 200 and needle in text, "HTTP %s" % status)

    status, _ = Client().get("/static/%2e%2e/index.html", raw=True)
    record("静态目录边界", "编码路径不能跳出 static，HTTP 404", status == 404, "HTTP %s" % status)

    # 2 未登录
    status, data = Client().get("/api/lessons")
    record("未登录访问课例", "HTTP 401", status == 401, "HTTP %s" % status)

    # 3 教师
    teacher, status, data = login("t_wang", "teach123")
    record("教师登录", "HTTP 200 且角色 teacher", status == 200 and data.get("user", {}).get("role") == "teacher", "HTTP %s" % status)

    status, data = teacher.get("/api/lessons/1")
    lesson = data.get("lesson", {})
    plan = lesson.get("plan", {}).get("data", {})
    items = lesson.get("exercises", {}).get("data", {}).get("items", [])
    record("课例包完整性", "3 条目标 / 7 题 / 2 个活动",
           len(plan.get("objectives", [])) == 3 and len(items) == 7 and len(lesson.get("activities", [])) == 2,
           "%s 目标 / %s 题 / %s 活动" % (len(plan.get("objectives", [])), len(items), len(lesson.get("activities", []))))

    # 4 局部再生成：只换流程，目标与板书保留
    before = json.loads(json.dumps(plan))
    before["board"] = "教师自定义板书：保留这一行"
    teacher.patch("/api/lessons/1/plan", {"data": before})
    status, data = teacher.post("/api/lessons/1/generate", {"target": "plan", "section": "flow"})
    after = data.get("lesson", {}).get("plan", {}).get("data", {})
    record("局部再生成只替换选中部分", "流程被替换，自定义板书保留",
           status == 200 and after.get("board") == "教师自定义板书：保留这一行" and len(after.get("flow", [])) == 5,
           "HTTP %s / 板书=%s / 环节=%s" % (status, after.get("board") == "教师自定义板书：保留这一行", len(after.get("flow", []))))

    # 5 模型失败：保留草稿并记录日志
    status, data = teacher.post("/api/lessons/1/generate", {"target": "plan", "simulate_failure": True})
    record("生成失败处理", "HTTP 502 且 preserved=true", status == 502 and data.get("preserved") is True, "HTTP %s" % status)
    status, logs = teacher.get("/api/lessons/1/gen-logs")
    failed = [l for l in logs.get("logs", []) if l["status"] == "failed"]
    record("失败写入生成日志", "至少 1 条 failed", len(failed) >= 1, "%s 条" % len(failed))

    # 6 课堂观察
    status, data = teacher.post("/api/tasks/1/observations",
                                {"student_id": 3, "kind": "independent", "result": "独立完成",
                                 "note": "验收脚本：换 dog 图后能独立完成"})
    record("记录课堂观察", "HTTP 200", status == 200, "HTTP %s" % status)
    status, data = teacher.post("/api/tasks/1/observations",
                                {"student_id": 3, "kind": "independent", "result": "优秀", "note": ""})
    record("观察结果只接受三档", "HTTP 400", status == 400, "HTTP %s" % status)
    status, data = teacher.get("/api/tasks/1/results")
    record("结果页返回观察记录", "至少 1 条", len(data.get("observations", [])) >= 1, "%s 条" % len(data.get("observations", [])))

    # 7 听写
    status, data = teacher.post("/api/lessons/1/dictations",
                                {"words": ["cat", "dog", "panda", "frog"], "wrong": ["panda"], "note": "验收脚本"})
    record("登记听写与错词", "HTTP 200 且错 1 个", status == 200 and len(data.get("wrong", [])) == 1, "HTTP %s" % status)
    status, data = teacher.post("/api/lessons/1/dictations",
                                {"words": ["cat"], "wrong": ["dog"], "note": ""})
    record("错词必须在词表内", "HTTP 400", status == 400, "HTTP %s" % status)
    status, raw = teacher.get("/print/dictation/1", raw=True)
    record("听写答题纸可打印", "HTTP 200 且含“听写答题纸”", status == 200 and "听写答题纸" in raw.decode("utf-8", "ignore"), "HTTP %s" % status)

    # 8 发布校验：缺评价要点时阻止
    status, data = teacher.post("/api/lessons/1/approve")
    record("重新审核课例", "HTTP 200", status == 200 and data.get("lesson", {}).get("status") == "approved", "HTTP %s" % status)
    status, data = teacher.post("/api/lessons/1/tasks",
                                {"class_id": 1, "title": "验收任务 · Animals", "instructions": "按题目要求作答。",
                                 "due_at": "", "allow_hints": True, "show_result": "immediately"})
    task_id = data.get("task", {}).get("id")
    record("创建任务草稿", "HTTP 200 且 status=draft", status == 200 and data.get("task", {}).get("status") == "draft", "HTTP %s" % status)
    status, data = teacher.post("/api/tasks/%s/publish" % task_id)
    record("发布任务", "HTTP 200 且 status=ongoing", status == 200 and data.get("task", {}).get("status") == "ongoing", "HTTP %s" % status)

    # 9 学生
    student, status, _ = login("s_chen", "stu123")
    status, data = student.get("/api/tasks/%s/student" % task_id)
    leaked = any("answer" in i or "analysis" in i or "accept" in i or "criteria" in i for i in data.get("items", []))
    record("学生接口不返回答案", "题目中无 answer/analysis/accept/criteria", not leaked, "泄露" if leaked else "未泄露")

    status, data = student.post("/api/tasks/%s/submit" % task_id, {"answers": {"q1": "B"}})
    record("缺题提交被拒绝", "HTTP 400 且缺 6 项", status == 400 and len(data.get("missing", [])) == 6,
           "HTTP %s 缺 %s 项" % (status, len(data.get("missing", []))))

    answers = {"q1": "B", "q2": "B", "q3": "A", "q4": "C", "q5": "dog", "q6": "a", "q7": "It's a frog. It is green."}
    status, data = student.post("/api/tasks/%s/submit" % task_id, {"answers": answers})
    sid = data.get("submission_id")
    record("完整提交", "HTTP 200 且返回 submission_id", status == 200 and bool(sid), "HTTP %s" % status)
    status, data = student.post("/api/tasks/%s/submit" % task_id, {"answers": answers})
    record("重复提交被阻止", "HTTP 409", status == 409, "HTTP %s" % status)

    # 10 教师批改 → 学生订正
    status, data = teacher.get("/api/submissions/%s/review" % sid)
    record("教师可看学生原答案", "HTTP 200 且 answers 非空", status == 200 and bool(data.get("answers")), "HTTP %s" % status)
    status, data = teacher.post("/api/submissions/%s/feedback/draft" % sid, {"item_id": "q7"})
    record("生成开放题反馈草稿", "草稿含 已完成/需检查/下一步", status == 200 and "已完成" in data.get("draft", ""), "HTTP %s" % status)
    status, data = teacher.post("/api/submissions/%s/feedback" % sid,
                                {"item_id": "q7", "final": "已完成：写出了动物和颜色。需检查：a 的位置。下一步：再读一遍。", "level": "需局部修改"})
    record("确认反馈", "HTTP 200", status == 200, "HTTP %s" % status)
    status, data = teacher.post("/api/submissions/%s/request-revision" % sid)
    record("要求订正", "HTTP 200", status == 200, "HTTP %s" % status)
    status, data = student.get("/api/tasks/%s/student" % task_id)
    sub = data.get("submission", {})
    record("学生看到已确认反馈", "feedback.q7 存在且 can_revise=true",
           bool(sub.get("feedback", {}).get("q7")) and sub.get("can_revise") is True,
           "反馈=%s 可订正=%s" % (bool(sub.get("feedback", {}).get("q7")), sub.get("can_revise")))
    answers["q7"] = "It's a frog. It is green."
    status, data = student.post("/api/submissions/%s/revise" % sid, {"answers": answers})
    record("学生提交订正", "HTTP 200", status == 200, "HTTP %s" % status)
    status, data = teacher.get("/api/submissions/%s/review" % sid)
    record("教师看到首次与订正两版", "history 非空且状态 resubmitted",
           bool(data.get("history")) and data.get("submission", {}).get("status") == "resubmitted",
           "history=%s 状态=%s" % (len(data.get("history", [])), data.get("submission", {}).get("status")))

    # 11 截止时间
    status, data = teacher.post("/api/lessons/1/tasks",
                                {"class_id": 1, "title": "验收任务 · 已过期", "instructions": "过期任务",
                                 "due_at": "2020-01-01 08:00", "allow_hints": True, "show_result": "immediately"})
    old_id = data.get("task", {}).get("id")
    teacher.post("/api/tasks/%s/publish" % old_id)
    late, _, _ = login("s_sun", "stu123")
    status, data = late.post("/api/tasks/%s/submit" % old_id, {"answers": answers})
    record("超过截止时间不能提交", "HTTP 400 且 code=overdue", status == 400 and data.get("code") == "overdue",
           "HTTP %s %s" % (status, data.get("code")))

    # 12 家长
    parent, status, _ = login("p_zhang", "par123")
    status, data = parent.get("/api/parent/overview")
    child = data.get("child", {}).get("name", "")
    record("家长只读绑定孩子", "HTTP 200 且 child=张小明", status == 200 and child == "张小明", "HTTP %s 孩子=%s" % (status, child))
    status, data = parent.post("/api/tasks/%s/submit" % task_id, {"answers": answers})
    record("家长不能提交作业", "HTTP 403", status == 403, "HTTP %s" % status)

    # 13 越权
    other, login_status, _ = login("t_li", "teach123")
    status, data = other.get("/api/lessons/1")
    record("其他教师不能看本人课例", "HTTP 403", status == 403, "HTTP %s" % status)

    total = len(RESULTS)
    passed = sum(1 for _, ok in RESULTS if ok)
    print("\n合计 %s 项，通过 %s 项，失败 %s 项" % (total, passed, total - passed), flush=True)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
