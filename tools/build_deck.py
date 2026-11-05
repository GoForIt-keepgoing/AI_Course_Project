# -*- coding: utf-8 -*-
"""生成答辩演示 PPTX（10 页）与配套截图。构建脚本，不参与应用运行。"""
from __future__ import annotations

import os
import shutil
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Emu, Inches, Pt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "交付物", "04_答辩材料")
SHOTS = os.path.join(ROOT, ".tmp", "shots")
if not os.path.isdir(SHOTS):
    # 没有新截图时，直接复用交付物里的截图，避免把图片从 PPTX 里丢掉
    SHOTS = os.path.join(OUT, "截图")

TEAL = RGBColor(0x0F, 0x76, 0x6E)
DARK = RGBColor(0x12, 0x30, 0x3A)
GRAY = RGBColor(0x5B, 0x6B, 0x73)
LIGHT = RGBColor(0xF1, 0xF5, 0xF9)
SOFT = RGBColor(0xE7, 0xF2, 0xF0)
AMBER = RGBColor(0xD9, 0x77, 0x06)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "微软雅黑"


def tx(slide, x, y, w, h, text, size=16, bold=False, color=DARK, align=PP_ALIGN.LEFT,
       anchor=MSO_ANCHOR.TOP, spacing=1.15):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.word_wrap = True
    frame.vertical_anchor = anchor
    frame.margin_left = 0
    frame.margin_right = 0
    frame.margin_top = 0
    frame.margin_bottom = 0
    lines = str(text).split("\n")
    for i, line in enumerate(lines):
        para = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        para.alignment = align
        para.line_spacing = spacing
        run = para.add_run()
        run.text = line
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color
        run.font.name = FONT
        from lxml import etree
        rpr = run._r.get_or_add_rPr()
        rpr.set("lang", "zh-CN")
        ns = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
        ea = rpr.find(ns + "ea")
        if ea is None:
            ea = etree.SubElement(rpr, ns + "ea")
        ea.set("typeface", FONT)
    return box


def rect(slide, x, y, w, h, fill, line=None, radius=False):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h))
    if radius:
        shape.adjustments[0] = 0.06
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(0.9)
    shape.shadow.inherit = False
    return shape


def new_slide(prs, title=None, kicker=None, page=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    rect(slide, 0, 0, 0.14, 7.5, TEAL)
    if kicker:
        tx(slide, 0.75, 0.5, 8, 0.3, kicker, 11, True, TEAL)
    if title:
        tx(slide, 0.75, 0.78, 11.8, 0.7, title, 28, True, DARK)
        rect(slide, 0.75, 1.52, 0.6, 0.045, AMBER)
    if page:
        tx(slide, 12.0, 6.95, 0.9, 0.3, str(page), 10, False, GRAY, PP_ALIGN.RIGHT)
        tx(slide, 0.75, 6.95, 8, 0.3, "AI4En · 面向英语教师的 AI 教学助手", 9, False, GRAY)
    return slide


def card(slide, x, y, w, h, head, body, label_color=TEAL, size=12.5):
    rect(slide, x, y, w, h, WHITE, RGBColor(0xE1, 0xE8, 0xEA), True)
    tx(slide, x + 0.22, y + 0.18, w - 0.44, 0.32, head, 13.5, True, DARK)
    tx(slide, x + 0.22, y + 0.58, w - 0.44, h - 0.72, body, size, False, GRAY, spacing=1.35)


def table(slide, x, y, w, rows, widths, height=0.36, head=True, size=10.5):
    cols = len(rows[0])
    shape = slide.shapes.add_table(len(rows), cols, Inches(x), Inches(y), Inches(w), Inches(height * len(rows)))
    tbl = shape.table
    for i, width in enumerate(widths):
        tbl.columns[i].width = Inches(width)
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            cell = tbl.cell(r, c)
            cell.text = ""
            cell.margin_left = Inches(0.08)
            cell.margin_right = Inches(0.06)
            cell.margin_top = Inches(0.03)
            cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = TEAL if (head and r == 0) else (WHITE if r % 2 else RGBColor(0xFA, 0xFC, 0xFC))
            para = cell.text_frame.paragraphs[0]
            run = para.add_run()
            run.text = str(value)
            run.font.size = Pt(size)
            run.font.name = FONT
            run.font.bold = head and r == 0
            run.font.color.rgb = WHITE if (head and r == 0) else DARK
    return shape


def build():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # 1 封面
    s = prs.slides.add_slide(prs.slide_layouts[6])
    rect(s, 0, 0, 13.333, 7.5, TEAL)
    rect(s, 0, 6.55, 13.333, 0.95, RGBColor(0x0B, 0x4F, 0x4A))
    tx(s, 0.95, 1.55, 10, 0.4, "AI4EN / COURSE PROJECT", 13, True, RGBColor(0xBF, 0xE6, 0xE0))
    tx(s, 0.95, 2.05, 11, 1.0, "AI4En：面向英语教师的 AI 教学助手", 40, True, WHITE)
    rect(s, 0.95, 3.42, 0.9, 0.06, AMBER)
    tx(s, 0.95, 3.75, 10.6, 1.1,
       "从备课到反馈的一条教学链路：一份课例 → 教案 / 课件 / 活动 / 练习 / 反馈 / 复盘",
       18, False, RGBColor(0xD3, 0xEC, 0xE7), spacing=1.5)
    tx(s, 0.95, 5.05, 11, 0.9,
       "小学三年级 · Animals（cat / dog / panda / frog）· 40 分钟\n教师主导 · 内容可编辑 · 结果可核对",
       13, False, RGBColor(0xBF, 0xE6, 0xE0), spacing=1.6)
    tx(s, 0.95, 6.78, 11.5, 0.4,
       "分工：A 后端与权限 · B 教师与学生页面 · C 备课与课堂资源 · D 练习与评价　|　2026.11", 11, False, RGBColor(0xBF, 0xE6, 0xE0))

    # 2 问题与目标
    s = new_slide(prs, "问题：材料割裂，反馈不可追踪", "01 / 问题与目标", 2)
    card(s, 0.75, 2.0, 3.7, 1.55, "材料割裂", "教案、课件、练习、作业反馈分散在多个工具里，改一处要同步四处。")
    card(s, 0.75, 3.75, 3.7, 1.55, "反馈不可追踪", "学生只看到分数；原始作答、教师确认、订正版本混在一起，家长也无从查看。")
    card(s, 0.75, 5.5, 3.7, 1.35, "AI 结果不敢直接用", "生成内容没有来源标记，成功生成被误当成“已通过教学审核”。")
    rect(s, 4.85, 2.0, 7.7, 4.85, RGBColor(0xF7, 0xFB, 0xFA), RGBColor(0xCF, 0xE6, 0xE2), True)
    tx(s, 5.15, 2.2, 7.1, 0.35, "本项目的三个目标", 14, True, TEAL)
    goals = [
        ("1", "一份课例贯穿五个环节", "教学条件只填一次，教案、课件、活动、练习与反馈共用同一组目标词句。"),
        ("2", "教师可控、可审核", "生成结果只作候选稿；修改、审核、发布每一步都由教师决定。"),
        ("3", "结果可核对", "客观题由代码判分；开放题由教师确认反馈；统计来自真实记录。"),
    ]
    for i, (num, head, body) in enumerate(goals):
        y = 2.7 + i * 1.36
        rect(s, 5.15, y + 0.02, 0.42, 0.42, TEAL, radius=True)
        tx(s, 5.15, y + 0.06, 0.42, 0.34, num, 13, True, WHITE, PP_ALIGN.CENTER)
        tx(s, 5.75, y, 6.5, 0.34, head, 14.5, True, DARK)
        tx(s, 5.75, y + 0.38, 6.5, 0.8, body, 12, False, GRAY, spacing=1.4)
    tx(s, 5.15, 6.2, 7.1, 0.5, "验收关注教学流程与可用产物，而不是菜单数量。", 11.5, True, AMBER)

    # 3 方案总览
    s = new_slide(prs, "一份课例，五类产物，三个角色", "02 / 方案总览", 3)
    tx(s, 0.75, 1.75, 4, 0.35, "课例（教学条件）", 13, True, TEAL)
    rect(s, 0.75, 2.15, 11.8, 0.95, SOFT, RGBColor(0xCF, 0xE6, 0xE2), True)
    tx(s, 0.95, 2.28, 3.4, 0.3, "三年级 · Animals · 40 分钟", 12.5, True, DARK)
    tx(s, 0.95, 2.62, 11.2, 0.3, "目标词 cat / dog / panda / frog　目标句 What's this? — It's a …　重点：问答配对与 a 的搭配", 11, False, GRAY)
    products = [
        ("教案", "目标 · 流程 · 板书\n检查方式与作业"),
        ("课件", "6 页固定模板\n可编辑 PPTX"),
        ("课堂活动", "词义配对 4 组\n句子排序 + 投屏"),
        ("练习与小测", "4 选 2 填 1 表达\n两种支持方式"),
        ("反馈与日志", "草稿 → 确认 → 订正\n统计与教学反思"),
    ]
    for i, (head, body) in enumerate(products):
        x = 0.75 + i * 2.4
        rect(s, x, 3.35, 2.15, 1.5, WHITE, RGBColor(0xE1, 0xE8, 0xEA), True)
        tx(s, x + 0.18, 3.5, 1.85, 0.32, head, 13, True, TEAL)
        tx(s, x + 0.18, 3.9, 1.85, 0.85, body, 10.5, False, GRAY, spacing=1.35)
    roles = [
        ("教师", "建课 · 生成 · 编辑 · 审核 · 发布 · 批改 · 导出", "本人课例与任教班级"),
        ("学生", "查看任务 · 提交 · 看已确认反馈 · 订正", "本人的任务与作答"),
        ("家长", "查看孩子任务、状态与已确认反馈（只读）", "绑定孩子的允许内容"),
    ]
    for i, (role, act, scope) in enumerate(roles):
        y = 4.95 + i * 0.58
        tx(s, 0.75, y, 0.8, 0.3, role, 11.5, True, DARK)
        tx(s, 1.6, y, 6.3, 0.3, act, 10.5, False, GRAY)
        tx(s, 8.1, y, 4.45, 0.3, scope, 10.5, False, TEAL)
    tx(s, 0.75, 6.55, 11.9, 0.3, "教师私有答案、未确认反馈与其他学生记录，不出现在学生或家长接口中。", 10, False, GRAY)

    # 4 演示路径
    s = new_slide(prs, "8 分钟连续演示：一条链路走完", "03 / 演示脚本", 4)
    steps = [
        ("1", "建课例", "填目标词句\n缺项有提示"), ("2", "改教案", "改一处活动时间\n保存草稿"),
        ("3", "开课件", "逐页编辑\n导出 PPTX"), ("4", "玩活动", "配对 / 排序\n投屏重玩"),
        ("5", "发任务", "预览学生页\n发布冻结快照"), ("6", "交作答", "学生提交\n重复提交被拒"),
        ("7", "确认反馈", "草稿 → 改写\n确认后可见"), ("8", "订正", "保留首次\n与订正两版"),
        ("9", "复盘", "统计 · 错题\n教学日志"),
    ]
    for i, (num, head, body) in enumerate(steps):
        col = i % 5
        row = i // 5
        x = 0.75 + col * 2.45
        y = 1.95 + row * 2.15
        rect(s, x, y, 2.2, 1.85, WHITE, RGBColor(0xE1, 0xE8, 0xEA), True)
        rect(s, x, y, 0.5, 0.42, TEAL, radius=True)
        tx(s, x, y + 0.05, 0.5, 0.3, num, 12, True, WHITE, PP_ALIGN.CENTER)
        tx(s, x + 0.65, y + 0.08, 1.45, 0.3, head, 13, True, DARK)
        tx(s, x + 0.2, y + 0.62, 1.85, 1.1, body, 10.5, False, GRAY, spacing=1.4)
    tx(s, 0.75, 6.35, 11.9, 0.55,
       "现场至少改一段内容或一道题并保存，证明系统确实可以编辑；PPTX 与 PDF 在演示电脑上实际打开。",
       11.5, False, GRAY)

    # 5 架构
    s = new_slide(prs, "实现：一个可运行的教学应用", "04 / 实现", 5)
    layers = [
        ("浏览器（无构建）", "原生 JS 单页应用：教师 / 学生 / 家长三端；登录、课例编辑、活动投屏、批改、统计。", "static/js · 5 个模块"),
        ("Python 服务（仅标准库）", "ThreadingHTTPServer + 路由 + 会话 + 权限；同一套接口服务三种角色；业务规则集中在 api.py。", "server.py · ai4en/api.py"),
        ("SQLite + 文件导出", "课例、任务快照、作答、反馈、日志分表保存；PPTX 用内置 OOXML 导出，PDF 走打印视图。", "data/ai4en.db · ppt_export.py"),
    ]
    for i, (head, body, tech) in enumerate(layers):
        y = 1.95 + i * 1.55
        rect(s, 0.75, y, 8.0, 1.32, WHITE, RGBColor(0xE1, 0xE8, 0xEA), True)
        tx(s, 0.98, y + 0.14, 5, 0.32, head, 13.5, True, DARK)
        tx(s, 0.98, y + 0.5, 7.55, 0.7, body, 10.5, False, GRAY, spacing=1.35)
        tx(s, 8.95, y + 0.14, 3.6, 0.3, tech, 9.5, False, TEAL)
    rect(s, 0.75, 6.55, 11.8, 0.75, SOFT, RGBColor(0xCF, 0xE6, 0xE2), True)
    tx(s, 0.95, 6.68, 11.4, 0.5,
       "模型调用只在后端：密钥不进浏览器；未配置模型时全部标记“示例内容”，可与真实调用清楚区分。",
       11, True, RGBColor(0x0B, 0x4F, 0x4A))

    # 6 产物
    s = new_slide(prs, "同一课例产出的可打开文件", "05 / 产物", 6)
    files = [
        ("教案.pdf", "A4 两页，目标/流程/板书/作业"),
        ("课件.pptx", "6 页可编辑文本，页序一致"),
        ("学生卷.pdf", "不含答案，可打印或课堂发放"),
        ("答案页.pdf", "仅教师可见，含解析与评价要点"),
        ("词卡任务卡.pdf", "4 张词卡 + 口头问答卡"),
        ("题库.xlsx", "题目、答案、统计与作答记录"),
    ]
    for i, (name, desc) in enumerate(files):
        col = i % 2
        row = i // 2
        x = 0.75 + col * 3.6
        y = 1.9 + row * 1.5
        rect(s, x, y, 3.4, 1.3, WHITE, RGBColor(0xE1, 0xE8, 0xEA), True)
        tx(s, x + 0.2, y + 0.16, 3.05, 0.3, name, 12.5, True, TEAL)
        tx(s, x + 0.2, y + 0.52, 3.05, 0.65, desc, 10, False, GRAY, spacing=1.3)
    pic = os.path.join(SHOTS, "04-lesson-slides.png")
    if os.path.exists(pic):
        s.shapes.add_picture(pic, Inches(8.05), Inches(1.9), height=Inches(3.3))
        tx(s, 8.05, 5.35, 4.6, 0.35, "课件资源页：逐页编辑 + 投屏预览", 9.5, False, GRAY)

    # 7 状态与权限
    s = new_slide(prs, "状态与权限：谁能看到什么", "06 / 数据与权限", 7)
    rows = [
        ["对象", "状态流转", "关键规则"],
        ["课例", "草稿 → 已审核", "修改教案或题目回到草稿；发布前必须已审核"],
        ["任务", "草稿 → 进行中 → 已结束", "发布时冻结题目与答案；改题复制为新任务"],
        ["学生作答", "未提交 → 已提交 → 待订正 → 已订正", "重复提交被拒绝；保留首次与订正两个版本"],
        ["开放题反馈", "草稿 → 已确认 → 学生可见", "确认后的修改保留原文，不覆盖"],
    ]
    table(s, 0.75, 1.95, 8.1, rows, [1.3, 3.0, 3.8], 0.36, size=10)
    tx(s, 0.75, 4.55, 8.1, 0.3, "接口级检查（不是只靠隐藏按钮）", 12.5, True, TEAL)
    checks = [
        "学生接口剥离 answer / analysis / accept 字段",
        "跨班学生、其他教师、他人孩子记录 → 403",
        "打印与导出需要登录；答案页仅教师",
        "未登录访问课例列表 → 401，失效即提示重新登录",
    ]
    for i, item in enumerate(checks):
        y = 4.95 + i * 0.42
        rect(s, 0.78, y + 0.11, 0.16, 0.16, TEAL, radius=True)
        tx(s, 1.1, y, 7.7, 0.32, item, 10.5, False, GRAY)
    tx(s, 9.15, 1.95, 3.4, 0.3, "演示账号", 12.5, True, TEAL)
    accounts = [["身份", "账号", "密码"], ["教师", "t_wang", "teach123"], ["学生", "s_zhang", "stu123"],
                ["家长", "p_zhang", "par123"], ["教师（对照）", "t_li", "teach123"]]
    table(s, 9.15, 2.35, 3.45, accounts, [1.15, 1.25, 1.05], 0.34, size=9.5)
    tx(s, 9.15, 5.0, 3.4, 1.5,
       "演示班级：三年级 2 班\n6 名学生，4 人已提交\n（2 人待交，用于统计）", 10, False, GRAY, spacing=1.5)

    # 8 验证
    s = new_slide(prs, "验证：先跑通，再说完成", "07 / 验证", 8)
    stats = [("45", "回归用例", "全部通过"), ("35", "整合验收", "全部通过"), ("5", "修复缺陷", "本轮发现并回归")]
    for i, (num, label, extra) in enumerate(stats):
        x = 0.75 + i * 2.55
        rect(s, x, 1.95, 2.35, 1.35, WHITE, RGBColor(0xE1, 0xE8, 0xEA), True)
        tx(s, x + 0.2, 2.08, 2.0, 0.55, num, 26, True, TEAL)
        tx(s, x + 0.2, 2.66, 2.0, 0.28, label, 10.5, True, DARK)
        tx(s, x + 0.2, 2.95, 2.0, 0.25, extra, 9.5, False, GRAY)
    rows = [
        ["覆盖项", "预期", "结果"],
        ["发布", "未审核或答案缺失时阻止发布并列出缺失项", "通过"],
        ["提交", "缺题、重复提交、超过截止时间都被拒绝", "通过"],
        ["权限", "跨班 / 他人课例 / 他人孩子 / 退出后旧会话 → 拒绝", "通过"],
        ["导出", "PPTX 6 页；9 个 PDF 文件头与页数正常", "通过"],
        ["生成失败", "502 + 提示保留草稿 + 失败写入日志", "通过"],
        ["整合", "“拓展”页内嵌工作坊/完整版 / 局部再生成 / 观察 / 听写", "通过"],
    ]
    table(s, 0.75, 3.5, 7.75, rows, [1.2, 5.0, 1.55], 0.31, size=9.5)
    tx(s, 0.75, 5.85, 7.75, 0.9,
       "两套脚本都用独立临时数据库，不影响演示数据；本轮据此修复了 5 个缺陷（详见“本次验证.md”）。\n"
       "手工验收覆盖界面、投屏、家长只读与文件实际打开。",
       10, False, GRAY, spacing=1.45)
    pic = os.path.join(SHOTS, "09-lesson-results.png")
    if os.path.exists(pic):
        s.shapes.add_picture(pic, Inches(8.75), Inches(1.95), height=Inches(3.45))
        tx(s, 8.75, 5.55, 4.3, 0.3, "结果页：提交率、单题错误率、待复核", 9.5, False, GRAY)

    # 9 来源与失败
    s = new_slide(prs, "生成内容：来源分清楚，失败可恢复", "08 / 模型与异常", 9)
    cols = [
        ("真实模型输出", "调用后端模型接口得到，页面标记“真实模型输出”，仅作候选稿。", "model"),
        ("示例内容", "未配置模型时使用预置模板，明确标记“示例内容”，不能作为真实调用的证据。", "sample"),
        ("规则 / 人工", "客观题判分、反馈草稿、教学反思由代码规则生成；教师修改记为“教师手工编辑”。", "rule"),
    ]
    for i, (head, body, tag) in enumerate(cols):
        x = 0.75 + i * 4.0
        rect(s, x, 1.95, 3.75, 1.95, WHITE, RGBColor(0xE1, 0xE8, 0xEA), True)
        tx(s, x + 0.22, 2.12, 3.3, 0.32, head, 13.5, True, TEAL)
        tx(s, x + 0.22, 2.52, 3.3, 1.2, body, 10.5, False, GRAY, spacing=1.4)
    tx(s, 0.75, 4.2, 6.0, 0.3, "失败时的处理", 12.5, True, TEAL)
    flow = ["调用失败", "保留输入与草稿", "显示原因与重试", "写入生成日志"]
    for i, item in enumerate(flow):
        x = 0.75 + i * 2.85
        rect(s, x, 4.6, 2.55, 0.7, SOFT, RGBColor(0xCF, 0xE6, 0xE2), True)
        tx(s, x, 4.72, 2.55, 0.45, item, 10.5, True, RGBColor(0x0B, 0x4F, 0x4A), PP_ALIGN.CENTER)
    tx(s, 0.75, 5.55, 11.8, 1.2,
       "课堂演示可点“演示：模型失败”，现场看到 502 提示、草稿仍在、日志新增一条 failed；\n"
       "答辩材料同时说明：本次演示未配置模型，所有生成内容为示例内容，不代表真实模型质量。",
       10.5, False, GRAY, spacing=1.5)

    # 10 局限与下一步
    s = new_slide(prs, "局限与下一步", "09 / 收尾", 10)
    tx(s, 0.75, 1.95, 5.6, 0.3, "已知局限", 13, True, TEAL)
    limits = [
        "只在三年级一个班试用（6 人），没有真实课堂的长期数据。",
        "模型未配置，生成内容全部为示例模板，质量不代表真实调用。",
        "家长端只读，不含消息与通知；学生端不支持附件与语音。",
        "PPTX 使用固定模板，复杂版式与图片仍需教师替换。",
    ]
    for i, item in enumerate(limits):
        y = 2.4 + i * 0.62
        rect(s, 0.78, y + 0.1, 0.14, 0.14, AMBER, radius=True)
        tx(s, 1.08, y, 5.2, 0.55, item, 10.5, False, GRAY, spacing=1.35)
    tx(s, 7.0, 1.95, 5.5, 0.3, "下一步", 13, True, TEAL)
    nexts = [
        "接入真实模型并做人工对比，保留失败率与耗时。",
        "用一个单元做完整试用，记录修改量与教师耗时。",
        "增加听力材料与错题复习的自动组卷。",
        "把权限校验扩展到多教师协作与班级共享。",
    ]
    for i, item in enumerate(nexts):
        y = 2.4 + i * 0.62
        rect(s, 7.03, y + 0.1, 0.14, 0.14, TEAL, radius=True)
        tx(s, 7.33, y, 5.2, 0.55, item, 10.5, False, GRAY, spacing=1.35)
    rect(s, 0.75, 5.5, 11.8, 1.1, RGBColor(0xF7, 0xFB, 0xFA), RGBColor(0xCF, 0xE6, 0xE2), True)
    tx(s, 0.98, 5.65, 11.4, 0.85,
       "一句话总结：AI4En 把“一份课例”变成一条可编辑、可审核、可追踪的教学链路——\n"
       "生成只是起点，教师的判断才是终点。",
       12.5, True, RGBColor(0x0B, 0x4F, 0x4A), spacing=1.5)

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "AI4En_答辩演示.pptx")
    props = prs.core_properties
    props.title = "AI4En：面向英语教师的 AI 教学助手 · 课堂答辩"
    props.subject = "AI4En 课程大作业 · 三年级 Animals 课例"
    props.author = "AI4En 课程项目组"
    props.keywords = "AI4En, 英语教学, 课例, 答辩"
    props.comments = "整合版答辩演示：教学助手 + AI 英语教学工作坊"
    prs.save(path)
    print("PPTX:", path, os.path.getsize(path), "bytes")


def copy_shots():
    target = os.path.join(OUT, "截图")
    os.makedirs(target, exist_ok=True)
    if os.path.normcase(os.path.abspath(SHOTS)) == os.path.normcase(os.path.abspath(target)):
        print("截图源即交付目录，跳过复制")
        return
    for name in ("02-teacher-home", "03-lesson-plan", "04-lesson-slides", "06-activity-present",
                 "09-lesson-results", "10-review", "11-guide", "13-student-task", "14-parent", "01-login"):
        source = os.path.join(SHOTS, name + ".png")
        if os.path.exists(source):
            shutil.copyfile(source, os.path.join(target, name + ".png"))
    print("截图已复制到", target)


if __name__ == "__main__":
    copy_shots()
    build()
