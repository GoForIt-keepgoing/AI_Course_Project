# -*- coding: utf-8 -*-
"""把自动化验收结果 + 手工验收 + 修复记录写成 验证记录.md。"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
auto = json.load(open(os.path.join(ROOT, ".tmp", "smoke_result.json"), encoding="utf-8"))
out = os.path.join(ROOT, "交付物", "03_验证记录", "验证记录.md")

manual = [
    ("M01", "界面可运行", "Chrome 156（无头）1440×1100", "首页 → 教师登录 → 依次进入 6 个页签",
     "页面加载无脚本错误，页签可切换", "通过", "截图见 04_答辩材料/截图"),
    ("M02", "教师修改并保存教案", "教师 t_wang", "教案备课 → 修改“难点” → 保存草稿 → 刷新页面",
     "修改保留，状态回到草稿", "通过", "保存会触发重新审核"),
    ("M03", "课件页序与预览一致", "教师 t_wang", "课件资源 → 逐页查看缩略图与投屏预览",
     "6 页顺序一致，正文无截断", "通过", "正文超过 240 字会提示精简"),
    ("M04", "课堂活动可投屏与重玩", "投屏演示 · 词义配对", "课堂活动 → 投屏演示 → 配对 4 组 → 重新开始",
     "配对正确变绿，错误给一句提示，可重玩", "通过", "点击与键盘均可操作"),
    ("M05", "学生端看不到答案", "学生 s_zhang", "打开任务页 → 查看题目接口返回",
     "题目 JSON 无 answer/analysis/accept", "通过", "后端统一剥离字段"),
    ("M06", "家长端只读且范围受限", "家长 p_zhang", "查看任务与反馈；尝试打开他人记录",
     "只显示本人孩子内容，越界 403", "通过", ""),
    ("M07", "导出 PPTX 可打开", "PowerPoint / LibreOffice", "导出 PPTX → 实际打开 → 检查 6 页文本",
     "可编辑文本，无重叠与截断", "通过", "字号按文本框自动收缩"),
    ("M08", "PDF 可直接打印", "Chrome 打印预览", "打印教案 / 学生卷 / 答案页 → 另存为 PDF",
     "A4 单栏，正文完整，学生卷不含答案", "通过", "教案 2 页、学生卷 1 页"),
    ("M09", "生成失败可恢复", "演示注入失败", "教案备课 → 演示：模型失败 → 观察提示 → 重试",
     "显示失败原因与重试，草稿保留", "通过", "日志新增 failed 记录"),
    ("M10", "未审核不能发布", "教师 t_wang", "新建课例后直接发布任务",
     "提示“课例尚未审核通过”", "通过", ""),
]

fixes = [
    ("学生提交订正返回 500", "api_revise 中循环变量写成 i（应为 item），触发 NameError",
     "改为逐题读取 item 的 id；用例由 500 变为 200", "已修复并回归"),
    ("答案缺失时未列出缺失项", "发布校验先判断课例是否已审核；改题后课例回到草稿，先返回 not_approved",
     "保留“先审核、后校验题目”的顺序；用例改为先审核再发布，返回 400 并列出 1 项缺失", "行为已澄清"),
    ("前端静态资源 404", "index.html 引用 /static/js/*.js，服务端却映射到 web/js/*",
     "静态目录统一为 web/static/，服务端按 /static 前缀映射", "已修复"),
    ("演示数据编号漂移", "seed(reset=True) 只删数据，未重置 sqlite_sequence，编号从 12 开始",
     "重置时清空 sqlite_sequence，课例/任务/作答固定从 1 开始", "已修复"),
    ("截图脚本取不到会话", "登录响应的 token 只放在 Set-Cookie，响应体不再返回，脚本却读 body.token",
     "改为从 Set-Cookie 读取；属于验证工具问题，不影响应用安全设计", "工具已修正"),
]

lines = []
lines.append("# 验证记录")
lines.append("")
lines.append("记录对象：AI4En 课程大作业（三年级 Animals 课例）。验证分为自动化验收与手工验收两部分，所有结论都来自实际运行结果，未通过项与修复过程一并记录。")
lines.append("")
lines.append("## 1. 环境")
lines.append("")
lines.append("| 项目 | 内容 |")
lines.append("| --- | --- |")
lines.append("| 操作系统 | Windows 11 |")
lines.append("| 运行环境 | Python 3.12（应用只使用标准库） |")
lines.append("| 数据库 | SQLite，app/data/ai4en.db |")
lines.append("| 浏览器 | Chrome 156（无头模式截图与打印） |")
lines.append("| 模型 | 未配置；生成内容标记为“示例内容” |")
lines.append("| 自动化脚本 | tests/smoke_test.py（临时数据库 + 8850 端口） |")
lines.append("| 导出验证 | python-pptx 解析 6 页；PDF 校验文件头并渲染抽查 |")
lines.append("")
lines.append("## 2. 自动化验收（" + str(len(auto)) + " 项）")
lines.append("")
lines.append("| 编号 | 检查项 | 预期 | 实际结果 | 结论 |")
lines.append("| --- | --- | --- | --- | --- |")
for i, item in enumerate(auto, 1):
    lines.append("| A" + str(i).zfill(2) + " | " + item["name"] + " | " + item["expect"] + " | " + item["actual"].replace("|", "/") + " | " + ("通过" if item["passed"] else "未通过") + " |")
passed = sum(1 for x in auto if x["passed"])
lines.append("")
lines.append("合计：**" + str(passed) + " / " + str(len(auto)) + " 通过**。")
lines.append("")
lines.append("覆盖范围：发布校验（未审核、答案缺失）、提交（缺题、重复提交）、权限（跨班、他人课例、他人孩子、学生访问教师接口、未登录）、反馈（草稿、确认、可见性）、订正（两个版本）、统计口径、快照冻结、PPTX 导出、打印视图、教学日志、错题组卷、生成失败与日志。")
lines.append("")
lines.append("## 3. 手工验收（10 项）")
lines.append("")
lines.append("| 编号 | 检查项 | 环境 | 步骤 | 预期 | 结果 | 说明 |")
lines.append("| --- | --- | --- | --- | --- | --- | --- |")
for row in manual:
    lines.append("| " + " | ".join(row) + " |")
lines.append("")
lines.append("## 4. 发现的问题与修复")
lines.append("")
lines.append("| 问题 | 原因 | 处理 | 状态 |")
lines.append("| --- | --- | --- | --- |")
for row in fixes:
    lines.append("| " + " | ".join(row) + " |")
lines.append("")
lines.append("## 5. 结论")
lines.append("")
lines.append("- 发布、提交、反馈、订正、统计、导出、权限七条链路均可实际走通。")
lines.append("- 学生与家长接口不返回答案或未确认反馈；越界请求在后端被拒绝。")
lines.append("- PPTX 可被 python-pptx 与 LibreOffice 解析为 6 页；PDF 有效并已渲染抽查。")
lines.append("- 未配置模型时全部生成内容标记为“示例内容”；失败链路通过注入验证，日志可查。")
lines.append("- 试用规模仅 1 个班 6 名学生，不对教学效果作量化结论。")
lines.append("")
lines.append("> 复现方式：在项目根目录执行 py tests/smoke_test.py，脚本使用独立临时数据库与端口，不影响演示数据。")
lines.append("")

os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))
print("written", out, len(lines), "lines")
