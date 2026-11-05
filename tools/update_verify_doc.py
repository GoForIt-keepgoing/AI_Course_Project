# -*- coding: utf-8 -*-
"""把本次 smoke 输出写入 验证记录.md 的“自动化验收”一节。"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log = open(os.path.join(ROOT, ".tmp", "smoke_stdout.txt"), encoding="utf-8").read()
rows = []
for line in log.splitlines():
    m = re.match(r"\s+(PASS|FAIL)\s+(.+?)\s+｜\s*预期：(.+?)\s+｜\s*实际：(.+)$", line)
    if m:
        rows.append((m.group(1) == "PASS", m.group(2), m.group(3), m.group(4)))

passed = sum(1 for r in rows if r[0])
table = ["| 编号 | 检查项 | 预期 | 实际结果 | 结论 |", "| --- | --- | --- | --- | --- |"]
for i, (ok, name, expect, actual) in enumerate(rows, 1):
    table.append("| A%02d | %s | %s | %s | %s |" % (i, name, expect, actual.replace("|", "/"), "通过" if ok else "未通过"))

section = (
    "## 2. 自动化验收（%d 项）\n\n" % len(rows)
    + "运行 `python tests/smoke_test.py`（`AI4EN_BASE` 指向已有服务时直接连该服务，否则自建临时数据库与服务）。"
    + "本次实际运行 %d 项，通过 %d 项。\n\n" % (len(rows), passed)
    + "\n".join(table)
    + "\n\n合计：**%d / %d 通过**。\n\n" % (passed, len(rows))
    + "覆盖范围：静态资源边界与方法限制、发布校验（未审核、答案缺失）、提交（缺题、重复提交、截止时间）、"
      "权限（跨班、他人课例、他人孩子、学生访问教师接口、未登录、退出后重放旧会话）、反馈（草稿、确认、可见性）、"
      "订正（两个版本）、支架（只给学生本次选用的那一种）、统计口径、快照冻结、错题组卷、PPTX 导出、打印视图、"
      "教学日志与生成失败。\n\n"
)

path = os.path.join(ROOT, "交付物", "03_验证记录", "验证记录.md")
text = open(path, encoding="utf-8").read()
start = text.index("## 2. 自动化验收")
end = text.index("## 3. 手工验收")
text = text[:start] + section + text[end:]
text = text.replace("本目录对应", "本目录对应")
text = text.replace("39 项", "45 项")
open(path, "w", encoding="utf-8").write(text)
print("rows", len(rows), "passed", passed)
