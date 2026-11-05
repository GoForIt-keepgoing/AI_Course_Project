# -*- coding: utf-8 -*-
"""交付物体检：文件、链接、PPTX、PDF 页数。"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "tools"))
import pdftext  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def rel(path):
    return os.path.relpath(path, ROOT).replace("\\", "/")


print("== 文件一览 ==")
for base, dirs, files in os.walk(os.path.join(ROOT, "交付物")):
    dirs.sort()
    for name in sorted(files):
        p = os.path.join(base, name)
        print("%9s  %s" % (os.path.getsize(p), rel(p)))

print("\n== PDF 页数 ==")
for base, dirs, files in os.walk(os.path.join(ROOT, "交付物")):
    for name in sorted(files):
        if name.lower().endswith(".pdf"):
            p = os.path.join(base, name)
            try:
                pages = len(pdftext.Doc(p).pages())
                head = open(p, "rb").read(5)
                print("%-70s pages=%-3s head=%s" % (rel(p), pages, head))
            except Exception as exc:
                print("%-70s ERROR %s" % (rel(p), exc))

print("\n== Markdown 链接检查 ==")
for base, dirs, files in os.walk(ROOT):
    if ".git" in base:
        continue
    for name in files:
        if not name.lower().endswith(".md"):
            continue
        p = os.path.join(base, name)
        text = open(p, encoding="utf-8", errors="ignore").read()
        for target in LINK.findall(text):
            target = target.split("#")[0].strip()
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = os.path.normpath(os.path.join(base, target.replace("/", os.sep)))
            if not os.path.exists(resolved):
                print("MISSING  %s -> %s" % (rel(p), target))

print("\n== PPTX ==")
try:
    from pptx import Presentation
    p = os.path.join(ROOT, "交付物", "04_答辩材料", "AI4En_答辩演示.pptx")
    prs = Presentation(p)
    print("slides:", len(prs.slides), "size:", os.path.getsize(p))
    for i, slide in enumerate(prs.slides, 1):
        texts = [sh.text_frame.text.strip().replace("\n", " / ") for sh in slide.shapes if sh.has_text_frame and sh.text_frame.text.strip()]
        print(" %2d  %s" % (i, " || ".join(texts)[:110]))
except Exception as exc:
    print("PPTX ERROR", exc)
