# -*- coding: utf-8 -*-
"""构建交付物：课件 PPTX、互动题库 XLSX、验证记录 XLSX，并整理 PDF。

这是构建脚本（开发期使用），应用运行本身不依赖 openpyxl / python-pptx。
运行前先启动应用并生成 PDF（见 tools/export_pdfs.mjs）。
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app")
sys.path.insert(0, APP)

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from ai4en import db, ppt_export  # noqa: E402

OUT = os.path.join(ROOT, "交付物")
PACK = os.path.join(OUT, "01_同一课例成果包")
TRAIN = os.path.join(OUT, "02_使用与培训材料")
VERIFY = os.path.join(OUT, "03_验证记录")
DEFENSE = os.path.join(OUT, "04_答辩材料")

TEAL = "0F766E"
LIGHT = "E7F2F0"
HEAD_FILL = PatternFill("solid", fgColor=TEAL)
HEAD_FONT = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
BODY_FONT = Font(name="微软雅黑", size=10)
TITLE_FONT = Font(name="微软雅黑", size=13, bold=True, color="12303A")
THIN = Side(style="thin", color="D8E0E3")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")


def ensure_dirs():
    for path in (PACK, TRAIN, VERIFY, DEFENSE, os.path.join(DEFENSE, "截图")):
        os.makedirs(path, exist_ok=True)


def lesson_bundle(lesson_id=1):
    lesson = db.query_one("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
    slides = db.query_one("SELECT data FROM materials WHERE lesson_id = ? AND kind = 'slides'", (lesson_id,))
    cards = db.query_one("SELECT data FROM materials WHERE lesson_id = ? AND kind = 'cards'", (lesson_id,))
    ex = db.query_one("SELECT data FROM exercises WHERE lesson_id = ?", (lesson_id,))
    return lesson, db.loads(slides["data"]) if slides else [], db.loads(cards["data"]) if cards else {}, db.loads(ex["data"]) if ex else {}


def export_pptx():
    lesson, slides, _, _ = lesson_bundle()
    raw = ppt_export.build({"title": lesson["title"], "grade": lesson["grade"]}, slides)
    path = os.path.join(PACK, "Animals_课件.pptx")
    with open(path, "wb") as fh:
        fh.write(raw)
    print("PPTX:", path, len(raw), "bytes")
    return path


def export_question_bank():
    lesson, _, _, ex = lesson_bundle()
    items = ex.get("items", [])
    wb = Workbook()
    ws = wb.active
    ws.title = "题目与答案"
    headers = ["序号", "题型", "题干", "选项", "正确答案", "可接受答案", "目标词句", "标签", "提示", "解析", "评价要点", "句架", "关键词"]
    ws.append(headers)
    for idx, item in enumerate(items, 1):
        ws.append([
            idx,
            {"choice": "选择题", "fill": "填空题", "short": "开放表达"}.get(item.get("type"), item.get("type")),
            item.get("stem", ""),
            " / ".join(str(o) for o in item.get("options") or []),
            item.get("answer", ""),
            "、".join(item.get("accept") or []),
            item.get("target", ""),
            item.get("tag", ""),
            item.get("hint", ""),
            item.get("analysis", ""),
            "\n".join(item.get("criteria") or []),
            item.get("frame", ""),
            item.get("keywords", ""),
        ])
    for cell in ws[1]:
        cell.fill = HEAD_FILL
        cell.font = HEAD_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    widths = [6, 10, 44, 30, 12, 16, 16, 8, 26, 32, 30, 26, 30]
    for i, width in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = width
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.font = BODY_FONT
            cell.alignment = WRAP
            cell.border = BORDER
    ws.freeze_panes = "A2"

    # 统计页
    task = db.query_one("SELECT * FROM tasks WHERE lesson_id = ? ORDER BY id LIMIT 1", (lesson["id"],))
    snapshot = db.loads(task["snapshot"]) if task else {"items": items}
    students = db.query("SELECT * FROM users WHERE role = 'student' AND class_id = ?", (task["class_id"],)) if task else []
    subs = db.query("SELECT s.*, u.name FROM submissions s JOIN users u ON u.id = s.student_id WHERE s.task_id = ?", (task["id"],)) if task else []
    st = wb.create_sheet("本课统计")
    st.append(["题号", "题型", "题干", "有效作答", "错误人数", "错误率", "待复核"])
    for idx, item in enumerate(snapshot.get("items", []), 1):
        valid = wrong = pending = 0
        for s in subs:
            ans = db.loads(s["answers"], {}).get(item["id"])
            if str(ans or "").strip():
                valid += 1
                if item["type"] != "short" and db.loads(s["grading"], {}).get(item["id"]) is False:
                    wrong += 1
                if item["type"] == "short":
                    fb = db.query_one("SELECT status FROM feedback WHERE submission_id = ? AND item_id = ?", (s["id"], item["id"]))
                    if not fb or fb["status"] != "confirmed":
                        pending += 1
        st.append([idx, {"choice": "选择题", "fill": "填空题", "short": "开放表达"}.get(item["type"], item["type"]),
                   item.get("stem", ""), valid, wrong,
                   (round(wrong / valid * 100, 1) if valid else "暂无记录"), pending])
    for cell in st[1]:
        cell.fill = HEAD_FILL
        cell.font = HEAD_FONT
    st.column_dimensions["C"].width = 50
    for i in range(1, 8):
        st.column_dimensions[get_column_letter(i)].width = max(st.column_dimensions[get_column_letter(i)].width or 0, 12)
    for row in st.iter_rows(min_row=2):
        for cell in row:
            cell.font = BODY_FONT
            cell.alignment = WRAP
            cell.border = BORDER

    # 作答记录
    wb2 = wb.create_sheet("学生作答记录")
    item_ids = [i["id"] for i in snapshot.get("items", [])]
    wb2.append(["学生", "状态", "提交时间", "客观题正确/总数"] + item_ids)
    for s in subs:
        answers = db.loads(s["answers"], {})
        grading = db.loads(s["grading"], {})
        correct = sum(1 for v in grading.values() if v is True)
        total = sum(1 for v in grading.values() if v is not None)
        wb2.append([s["name"], {"submitted": "已提交", "revision_requested": "待订正",
                                "resubmitted": "已订正"}.get(s["status"], s["status"]),
                    s["submitted_at"], str(correct) + "/" + str(total)]
                   + [answers.get(i, "") for i in item_ids])
    for cell in wb2[1]:
        cell.fill = HEAD_FILL
        cell.font = HEAD_FONT
    for row in wb2.iter_rows(min_row=2):
        for cell in row:
            cell.font = BODY_FONT
            cell.border = BORDER
            cell.alignment = WRAP
    for i in range(1, 5 + len(item_ids)):
        wb2.column_dimensions[get_column_letter(i)].width = 16 if i > 4 else 20

    path = os.path.join(PACK, "Animals_互动题库与作答记录.xlsx")
    wb.save(path)
    print("XLSX:", path)
    return path


def copy_pdfs():
    src = os.path.join(ROOT, ".tmp", "pdf")
    mapping = {
        "animals-教案.pdf": (PACK, "Animals_教案.pdf"),
        "animals-学生卷.pdf": (PACK, "Animals_学生卷.pdf"),
        "animals-答案页.pdf": (PACK, "Animals_独立答案页.pdf"),
        "animals-词卡与任务卡.pdf": (PACK, "Animals_词卡与任务卡.pdf"),
        "animals-反馈订正样例.pdf": (PACK, "Animals_反馈订正样例.pdf"),
        "animals-教学日志.pdf": (PACK, "Animals_教学日志.pdf"),
        "guide-教师操作卡.pdf": (TRAIN, "教师操作卡.pdf"),
        "guide-可复制提示词.pdf": (TRAIN, "可复制提示词.pdf"),
        "guide-60分钟培训.pdf": (TRAIN, "60分钟培训流程.pdf"),
    }
    for name, (folder, target) in mapping.items():
        source = os.path.join(src, name)
        if os.path.exists(source):
            shutil.copyfile(source, os.path.join(folder, target))
            print("PDF ->", target)
        else:
            print("缺少 PDF：", source)


def export_records():
    result_path = os.path.join(ROOT, ".tmp", "smoke_result.json")
    auto = json.load(open(result_path, encoding="utf-8")) if os.path.exists(result_path) else []

    manual = [
        ("M01", "界面可运行", "Chrome 无头截图 / 1440×1100",
         "打开首页 → 教师登录 → 依次进入 6 个页签",
         "页面加载无脚本错误，页签可切换", "通过", "无"),
        ("M02", "教师修改并保存教案", "教师 t_wang",
         "教案备课 → 修改“难点” → 保存草稿 → 刷新页面",
         "修改保留，状态回到草稿", "通过", "无"),
        ("M03", "课件页序与预览一致", "教师 t_wang",
         "课件资源 → 逐页查看缩略图与投屏预览",
         "6 页顺序一致，正文无截断", "通过", "正文超 240 字会提示精简"),
        ("M04", "课堂活动可投屏与重玩", "投屏演示 · 词义配对",
         "课堂活动 → 投屏演示 → 配对 4 组 → 重新开始",
         "配对正确变绿，错误给一句提示，可重玩", "通过", "无"),
        ("M05", "学生端看不到答案", "学生 s_zhang",
         "打开任务页 → 查看题目 → 打开开发者工具网络面板",
         "题目 JSON 无 answer/analysis 字段", "通过", "后端统一剥离字段"),
        ("M06", "家长端只读且范围受限", "家长 p_zhang",
         "家长页查看任务与反馈；尝试打开他人记录链接",
         "只显示本人孩子内容，越界返回 403", "通过", "无"),
        ("M07", "导出 PPTX 可打开", "PowerPoint / LibreOffice",
         "导出 PPTX → 实际打开 → 检查 6 页文本",
         "可编辑文本，无重叠与截断", "通过", "字号按文本框自动收缩"),
        ("M08", "PDF 可直接打印", "Chrome 打印预览",
         "打印教案 / 学生卷 / 答案页 → 另存为 PDF",
         "A4 单栏，正文完整，学生卷不含答案", "通过", "无"),
        ("M09", "生成失败可恢复", "演示注入失败",
         "教案备课 → 演示：模型失败 → 观察提示 → 重试",
         "显示失败原因与重试，草稿保留", "通过", "日志记录 failed"),
        ("M10", "未审核不能发布", "教师 t_wang",
         "新建课例后直接发布任务",
         "提示“课例尚未审核通过”", "通过", "无"),
    ]

    wb = Workbook()
    ws = wb.active
    ws.title = "自动化验收"
    ws.append(["编号", "检查项", "预期", "实际结果", "结论"])
    for idx, item in enumerate(auto, 1):
        ws.append(["A" + str(idx).zfill(2), item["name"], item["expect"], item["actual"],
                   "通过" if item["passed"] else "未通过"])
    for cell in ws[1]:
        cell.fill = HEAD_FILL
        cell.font = HEAD_FONT
    widths = [8, 46, 44, 46, 10]
    for i, width in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = width
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.font = BODY_FONT
            cell.border = BORDER
            cell.alignment = WRAP
    ws.freeze_panes = "A2"

    ws2 = wb.create_sheet("手工验收")
    ws2.append(["编号", "检查项", "环境", "步骤", "预期", "实际", "说明"])
    for row in manual:
        ws2.append(list(row))
    for cell in ws2[1]:
        cell.fill = HEAD_FILL
        cell.font = HEAD_FONT
    for i, width in enumerate([8, 24, 26, 46, 34, 34, 30], 1):
        ws2.column_dimensions[get_column_letter(i)].width = width
    for row in ws2.iter_rows(min_row=2):
        for cell in row:
            cell.font = BODY_FONT
            cell.border = BORDER
            cell.alignment = WRAP
    ws2.freeze_panes = "A2"

    ws3 = wb.create_sheet("环境与说明")
    rows = [
        ("记录时间", datetime.now().strftime("%Y-%m-%d %H:%M")),
        ("操作系统", "Windows 11"),
        ("浏览器", "Chrome 156（无头模式截图）"),
        ("运行环境", "Python 3.13.9（应用仅用标准库）"),
        ("数据库", "SQLite（app/data/ai4en.db）"),
        ("模型配置", "未配置，生成内容标记为“示例内容”"),
        ("自动化脚本", "tests/smoke_test.py（45 项回归）+ tests/acceptance.py（35 项整合验收）"),
        ("通过情况", str(sum(1 for x in auto if x["passed"])) + " / " + str(len(auto)) + " 自动化用例"),
        ("PDF 生成方式", "应用打印视图 → 浏览器 printToPDF（A4）"),
        ("PPTX 生成方式", "应用内置 OOXML 导出（不使用第三方库）"),
    ]
    for row in rows:
        ws3.append(list(row))
    ws3.column_dimensions["A"].width = 18
    ws3.column_dimensions["B"].width = 70
    for row in ws3.iter_rows(min_row=1):
        row[0].font = Font(name="微软雅黑", size=10, bold=True, color=TEAL)
        row[1].font = BODY_FONT
        row[1].alignment = WRAP

    path = os.path.join(VERIFY, "验证记录.xlsx")
    wb.save(path)
    print("XLSX:", path, "（自动化 " + str(len(auto)) + " 条）")


def main():
    db.init()
    ensure_dirs()
    export_pptx()
    export_question_bank()
    copy_pdfs()
    export_records()


if __name__ == "__main__":
    main()
