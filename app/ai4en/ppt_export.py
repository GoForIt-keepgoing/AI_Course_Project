# -*- coding: utf-8 -*-
"""纯标准库 PPTX 导出：固定模板、可编辑文本、按文本框自动选字号。

不依赖 python-pptx，导出结果是一份完整的 OOXML 包（slideMaster / slideLayout / theme），
可直接在 PowerPoint、WPS、LibreOffice 中打开编辑。
"""
from __future__ import annotations

import io
import math
import zipfile
from datetime import datetime, timezone

EMU = 12700  # 1pt = 12700 EMU
SLIDE_W = 12192000
SLIDE_H = 6858000
FONT = "Microsoft YaHei"
TEAL = "0F766E"
DARK = "12303A"
GRAY = "5B6B73"
LIGHT = "F1F5F9"
ACCENT = "F59E0B"

NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
REL_NS = 'xmlns="http://schemas.openxmlformats.org/package/2006/relationships"'
RT = {
    "office": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
    "slide": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide",
    "master": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster",
    "layout": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout",
    "theme": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme",
}
CT = "application/vnd.openxmlformats-officedocument.presentationml."


def esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def _is_cjk(ch):
    code = ord(ch)
    return (0x2E80 <= code <= 0x9FFF) or (0xF900 <= code <= 0xFAFF) or (0xFF00 <= code <= 0xFF60) or (0x3000 <= code <= 0x303F)


def text_width_em(text):
    return sum(1.0 if _is_cjk(ch) else 0.55 for ch in text)


def fit_size(text, width_pt, height_pt, max_size=26, min_size=12):
    for size in range(max_size, min_size - 1, -1):
        lines = 0
        for para in str(text).split("\n"):
            per_line = max(1.0, width_pt / max(size, 1))
            lines += max(1, math.ceil(text_width_em(para) / per_line))
        if lines * size * 1.34 <= height_pt:
            return size
    return min_size


def run(text, size, bold=False, color=DARK, font=FONT):
    b = ' b="1"' if bold else ""
    return ('<a:r><a:rPr lang="zh-CN" sz="' + str(int(size * 100)) + '"' + b + ' dirty="0">'
            '<a:solidFill><a:srgbClr val="' + color + '"/></a:solidFill>'
            '<a:latin typeface="' + font + '"/><a:ea typeface="' + font + '"/><a:cs typeface="' + font + '"/>'
            '</a:rPr><a:t>' + esc(text) + "</a:t></a:r>")


def paragraph(text, size, bold=False, color=DARK, space_before=0, align="l", line_pct=100000):
    ppr = ('<a:pPr algn="' + align + '"><a:lnSpc><a:spcPct val="' + str(line_pct) + '"/></a:lnSpc>'
           '<a:spcBef><a:spcPts val="' + str(int(space_before * 100)) + '"/></a:spcBef>'
           '<a:buNone/></a:pPr>')
    if text == "":
        return "<a:p>" + ppr + '<a:endParaRPr lang="zh-CN" sz="' + str(int(size * 100)) + '"/></a:p>'
    return "<a:p>" + ppr + run(text, size, bold, color) + "</a:p>"


def text_box(sid, name, x, y, cx, cy, paras, anchor="t", insets=(0, 0, 0, 0)):
    body = ('<a:bodyPr wrap="square" lIns="' + str(insets[0]) + '" tIns="' + str(insets[1]) +
            '" rIns="' + str(insets[2]) + '" bIns="' + str(insets[3]) + '" anchor="' + anchor + '">'
            '<a:normAutofit/></a:bodyPr><a:lstStyle/>')
    return ('<p:sp><p:nvSpPr><p:cNvPr id="' + str(sid) + '" name="' + esc(name) + '"/>'
            '<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            '<p:spPr><a:xfrm><a:off x="' + str(int(x)) + '" y="' + str(int(y)) + '"/>'
            '<a:ext cx="' + str(int(cx)) + '" cy="' + str(int(cy)) + '"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
            '<p:txBody>' + body + "".join(paras) + "</p:txBody></p:sp>")


def rect(sid, name, x, y, cx, cy, color):
    return ('<p:sp><p:nvSpPr><p:cNvPr id="' + str(sid) + '" name="' + esc(name) + '"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            '<p:spPr><a:xfrm><a:off x="' + str(int(x)) + '" y="' + str(int(y)) + '"/>'
            '<a:ext cx="' + str(int(cx)) + '" cy="' + str(int(cy)) + '"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            '<a:solidFill><a:srgbClr val="' + color + '"/></a:solidFill><a:ln><a:noFill/></a:ln></p:spPr>'
            '<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="zh-CN"/></a:p></p:txBody></p:sp>')


def sp_tree(shapes):
    return ('<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
            '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
            + "".join(shapes) + "</p:spTree>")


def slide_xml(shapes):
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
            '<p:sld ' + NS + '><p:cSld>' + sp_tree(shapes) + '</p:cSld>'
            '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')


def build_content_slide(index, total, footer, slide):
    width_pt = (10363200) / EMU
    height_pt = (4100000) / EMU
    title = str(slide.get("title") or "")
    body = str(slide.get("body") or "")
    subtitle = str(slide.get("subtitle") or "")
    t_size = max(24, min(34, fit_size(title, width_pt, 60, 34, 24)))
    b_size = fit_size(body, width_pt - 6, height_pt * 0.88, 26, 13)

    shapes = [
        rect(2, "左侧色条", 0, 0, 91440, SLIDE_H, TEAL),
        rect(3, "标题下划线", 571500, 1_410_000, 685800, 38100, ACCENT),
        text_box(4, "标题", 571500, 500000, 10600000, 800000,
                 [paragraph(title, t_size, True, DARK, 0, "l")]),
        text_box(5, "正文", 571500, 1_620_000, 10363200 if not subtitle else 10363200, 4_100_000,
                 [paragraph(line, b_size, False, DARK, 0 if i == 0 else 8, "l")
                  for i, line in enumerate(body.split("\n"))]),
        text_box(6, "页脚", 571500, 6_250_000, 8000000, 260000,
                 [paragraph(footer, 10, False, GRAY, 0, "l")]),
        text_box(7, "页码", 10600000, 6_250_000, 1000000, 260000,
                 [paragraph(str(index) + " / " + str(total), 10, False, GRAY, 0, "r")]),
    ]
    if subtitle:
        shapes.append(text_box(8, "副标题", 571500, 1_500_000, 10363200, 320000,
                               [paragraph(subtitle, 13, False, GRAY, 0, "l")]))
    return slide_xml(shapes)


def build_cover_slide(index, total, lesson, slide):
    title = str(slide.get("title") or lesson.get("title") or "")
    subtitle = str(slide.get("subtitle") or "")
    body = str(slide.get("body") or "")
    shapes = [
        rect(2, "左侧色条", 0, 0, 160020, SLIDE_H, TEAL),
        rect(3, "底部色块", 0, 6_300_000, SLIDE_W, 558000, LIGHT),
        text_box(4, "主标题", 914400, 1_400_000, 10100000, 1_600_000,
                 [paragraph(title, max(30, min(44, fit_size(title, 760, 120, 44, 30))), True, DARK, 0, "l")]),
        text_box(5, "副标题", 914400, 2_900_000, 10100000, 400000,
                 [paragraph(subtitle, 16, False, TEAL, 0, "l")]),
        text_box(6, "首页正文", 914400, 3_500_000, 10100000, 2_500_000,
                 [paragraph(line, 20 if i == 0 else 17, i == 0, DARK if i == 0 else GRAY, 0 if i == 0 else 12, "l")
                  for i, line in enumerate(body.split("\n"))]),
        text_box(7, "页脚", 914400, 6_400_000, 8000000, 300000,
                 [paragraph("AI4En · 教师主导 · 内容可编辑 · 结果可核对", 11, False, GRAY, 0, "l")]),
        text_box(8, "页码", 10600000, 6_400_000, 1000000, 300000,
                 [paragraph(str(index) + " / " + str(total), 11, False, GRAY, 0, "r")]),
    ]
    return slide_xml(shapes)


def theme_xml():
    accents = ["0F766E", "F59E0B", "115E59", "0EA5A4", "94A3B8", "12303A"]
    clr = ['<a:dk1><a:srgbClr val="' + DARK + '"/></a:dk1>',
           '<a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>',
           '<a:dk2><a:srgbClr val="0B4F4A"/></a:dk2>',
           '<a:lt2><a:srgbClr val="' + LIGHT + '"/></a:lt2>']
    clr += ['<a:accent' + str(i + 1) + '><a:srgbClr val="' + c + '"/></a:accent' + str(i + 1) + '>'
            for i, c in enumerate(accents)]
    clr += ['<a:hlink><a:srgbClr val="0F766E"/></a:hlink>',
            '<a:folHlink><a:srgbClr val="115E59"/></a:folHlink>']
    solid = '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    ln = ('<a:ln w="6350" cap="flat" cmpd="sng" algn="ctr">' + solid +
          '<a:prstDash val="solid"/><a:miter lim="800000"/></a:ln>')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
            '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="AI4En">'
            '<a:themeElements><a:clrScheme name="AI4En">' + "".join(clr) + '</a:clrScheme>'
            '<a:fontScheme name="AI4En">'
            '<a:majorFont><a:latin typeface="' + FONT + '"/><a:ea typeface="' + FONT + '"/><a:cs typeface=""/></a:majorFont>'
            '<a:minorFont><a:latin typeface="' + FONT + '"/><a:ea typeface="' + FONT + '"/><a:cs typeface=""/></a:minorFont>'
            '</a:fontScheme>'
            '<a:fmtScheme name="AI4En">'
            '<a:fillStyleLst>' + solid * 3 + '</a:fillStyleLst>'
            '<a:lnStyleLst>' + ln * 3 + '</a:lnStyleLst>'
            '<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle>'
            '<a:effectStyle><a:effectLst/></a:effectStyle>'
            '<a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>'
            '<a:bgFillStyleLst>' + solid * 3 + '</a:bgFillStyleLst>'
            '</a:fmtScheme></a:themeElements>'
            '<a:objectDefaults/><a:extraClrSchemeLst/></a:theme>')

def master_xml():
    shapes = [rect(2, "背景装饰", 0, 0, SLIDE_W, 76200, TEAL)]
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
            '<p:sldMaster ' + NS + '><p:cSld>' + sp_tree(shapes) + '</p:cSld>'
            '<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" '
            'accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
            '<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>'
            '<p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>')


def layout_xml():
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
            '<p:sldLayout ' + NS + ' type="blank" preserve="1"><p:cSld name="Blank">'
            + sp_tree([]) + '</p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')


def rels(items):
    body = "".join('<Relationship Id="' + rid + '" Type="' + rtype + '" Target="' + target + '"/>'
                   for rid, rtype, target in items)
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
            '<Relationships ' + REL_NS + '>' + body + "</Relationships>")


def build(lesson, slides):
    """slides: [{title, subtitle?, body}] → PPTX bytes。"""
    slides = [s for s in (slides or []) if str(s.get("title") or "").strip()]
    if not slides:
        slides = [{"title": lesson.get("title", "AI4En 课件"), "body": ""}]
    total = len(slides)
    footer = "AI4En · " + str(lesson.get("title", "")) + " · " + str(lesson.get("grade", ""))
    slide_parts = []
    for idx, slide in enumerate(slides, 1):
        if idx == 1:
            slide_parts.append(build_cover_slide(idx, total, lesson, slide))
        else:
            slide_parts.append(build_content_slide(idx, total, footer, slide))

    n = len(slides)
    pres_rels = [("rId1", RT["master"], "slideMasters/slideMaster1.xml")]
    for i in range(n):
        pres_rels.append(("rId" + str(i + 2), RT["slide"], "slides/slide" + str(i + 1) + ".xml"))
    pres_rels.append(("rId" + str(n + 2), RT["theme"], "theme/theme1.xml"))

    sld_ids = "".join('<p:sldId id="' + str(256 + i) + '" r:id="rId' + str(i + 2) + '"/>' for i in range(n))
    presentation = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
                    '<p:presentation ' + NS + ' saveSubsetFonts="1">'
                    '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
                    '<p:sldIdLst>' + sld_ids + '</p:sldIdLst>'
                    '<p:sldSz cx="' + str(SLIDE_W) + '" cy="' + str(SLIDE_H) + '"/>'
                    '<p:notesSz cx="6858000" cy="9144000"/></p:presentation>')

    overrides = [
        ('/ppt/presentation.xml', CT + 'presentation.main+xml'),
        ('/ppt/slideMasters/slideMaster1.xml', CT + 'slideMaster+xml'),
        ('/ppt/slideLayouts/slideLayout1.xml', CT + 'slideLayout+xml'),
        ('/ppt/theme/theme1.xml', 'application/vnd.openxmlformats-officedocument.theme+xml'),
    ]
    for i in range(n):
        overrides.append(('/ppt/slides/slide' + str(i + 1) + '.xml', CT + 'slide+xml'))
    content_types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
                     '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                     '<Default Extension="xml" ContentType="application/xml"/>'
                     + "".join('<Override PartName="' + p + '" ContentType="' + c + '"/>' for p, c in overrides)
                     + '</Types>')

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels([("rId1", RT["office"], "ppt/presentation.xml")]))
        z.writestr("docProps/core.xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
                   '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
                   'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
                   'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
                   '<dc:title>' + esc(lesson.get("title", "")) + '</dc:title>'
                   '<dc:creator>AI4En</dc:creator>'
                   '<dcterms:created xsi:type="dcterms:W3CDTF">' + stamp + '</dcterms:created>'
                   '<dcterms:modified xsi:type="dcterms:W3CDTF">' + stamp + '</dcterms:modified>'
                   '</cp:coreProperties>')
        z.writestr("ppt/presentation.xml", presentation)
        z.writestr("ppt/_rels/presentation.xml.rels", rels(pres_rels))
        z.writestr("ppt/slideMasters/slideMaster1.xml", master_xml())
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels",
                   rels([("rId1", RT["layout"], "../slideLayouts/slideLayout1.xml"),
                         ("rId2", RT["theme"], "../theme/theme1.xml")]))
        z.writestr("ppt/slideLayouts/slideLayout1.xml", layout_xml())
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels",
                   rels([("rId1", RT["master"], "../slideMasters/slideMaster1.xml")]))
        z.writestr("ppt/theme/theme1.xml", theme_xml())
        for i, xml in enumerate(slide_parts, 1):
            z.writestr("ppt/slides/slide" + str(i) + ".xml", xml)
            z.writestr("ppt/slides/_rels/slide" + str(i) + ".xml.rels",
                       rels([("rId1", RT["layout"], "../slideLayouts/slideLayout1.xml")]))
    return buf.getvalue()
