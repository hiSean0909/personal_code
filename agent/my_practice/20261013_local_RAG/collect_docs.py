# -*- coding: utf-8 -*-
"""collect_docs.py — 开发期一次性脚本：将已下载的网页源文件转换为知识库文件。

输入：knowledge_base/html/（交付用 HTML，兼作源文件）+ knowledge_base/_work/raw/（中间源文件）
输出：knowledge_base/{txt,md,docx,pdf}/ 下的 12 份文档
运行：python collect_docs.py
"""

import re
from pathlib import Path

from bs4 import BeautifulSoup
from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

BASE = Path(__file__).parent
KB = BASE / "knowledge_base"
RAW = KB / "_work" / "raw"
FONT = r"C:\Windows\Fonts\simhei.ttf"

# ---------- HTML 解析 ----------


def soup_of(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_bytes(), "lxml")


def clean_mediawiki(root, soup) -> None:
    """移除与正文无关的元素（导航、引用、表格、编辑链接等）。"""
    for sel in (
        "script", "style", "table", "nav", "figure", "sup",
        ".mw-editsection", ".reference", ".navbox", ".toc", "#toc",
        ".infobox", ".thumb", ".hatnote", ".shortdescription",
        ".metadata", ".reflist", ".mw-references-wrap", ".nav",
        ".mw-jump-link", ".printfooter", ".catlinks",
    ):
        for el in root.select(sel):
            el.decompose()


SKIP_H2 = re.compile(
    r"^(參見|参见|注[釋释]|参考|参考文獻|參考文獻|参考文献|延伸[阅閱]讀|延伸阅读|外部[连連]接|外部链接|参考资[料料]|来源|研究与评价)"
)


def wiki_blocks(path: Path, cap: int = 10**9) -> list[tuple[str, str]]:
    """提取 MediaWiki 条目正文，返回 [('h2'|'h3'|'p'|'li', 文本), ...]。

    cap: 累计字符上限，超出即停止（按整块累加）。
    """
    soup = soup_of(path)
    root = soup.select_one("#mw-content-text .mw-parser-output") or soup.select_one(".mw-parser-output")
    if root is None:
        raise RuntimeError(f"mw-parser-output not found: {path}")
    clean_mediawiki(root, soup)

    blocks: list[tuple[str, str]] = []
    total = 0
    for el in root.find_all(["h2", "h3", "p", "ul", "ol"], recursive=True):
        text = el.get_text(" ", strip=True)
        if not text:
            continue
        if el.name == "h2":
            if SKIP_H2.match(text):
                continue
            blocks.append(("h2", text))
        elif el.name == "h3":
            blocks.append(("h3", text))
        elif el.name in ("ul", "ol"):
            for li in el.find_all("li", recursive=False):
                t = li.get_text(" ", strip=True)
                if t:
                    blocks.append(("li", t))
                    total += len(t)
            continue
        else:
            blocks.append(("p", text))
        total += len(text)
        if total >= cap:
            break
    return blocks


def wiki_title(path: Path) -> str:
    soup = soup_of(path)
    h = soup.select_one("#firstHeading")
    return h.get_text(strip=True) if h else path.stem


def wikisource_text(path: Path) -> str:
    """提取维基文库正文（如《史记》《汉书》原文）。"""
    soup = soup_of(path)
    root = soup.select_one("#mw-content-text .mw-parser-output") or soup.select_one(".mw-parser-output")
    clean_mediawiki(root, soup)
    lines = []
    for p in root.find_all("p"):
        t = p.get_text("\n", strip=True)
        t = re.sub(r"\[\d+\]", "", t)  # 去掉引用角标
        for line in t.split("\n"):
            line = line.strip()
            if line and not line.startswith("↑"):
                lines.append(line)
    return "\n\n".join(lines)


FOLKLORE_JUNK = re.compile(
    r"^(【|首页|民俗学文库|研究论文|上一条|下一条|返回|打印|关闭|TOP|\||文章来源|【本文责编|继续浏览|\d+$|中国民俗学会|・|研究综述|田野报告|书评|专著|访谈|学者|译著|民俗影像|民俗学刊物)"
)


def folklore_text() -> str:
    """拼接 chinafolklore.org 文章全部 11 页正文。"""
    parts = []
    files = [RAW / "汉武帝从历史人物到小说形象.html"] + [
        RAW / f"folklore_p{i}.html" for i in range(2, 12)
    ]
    for f in files:
        soup = soup_of(f)
        text = soup.body.get_text("\n", strip=True)
        m = re.search(r"点击数：\d+", text)
        start = m.end() if m else 0
        end = text.find("继续浏览")
        if end == -1:
            end = len(text)
        chunk = text[start:end]
        lines = [
            ln.strip()
            for ln in chunk.split("\n")
            if ln.strip() and not FOLKLORE_JUNK.match(ln.strip())
        ]
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


# ---------- 输出工具 ----------


def write_txt(out: Path, text: str) -> None:
    out.write_text(text, encoding="utf-8")


def write_markdown(out: Path, title: str, blocks: list[tuple[str, str]]) -> None:
    lines = [f"# {title}", ""]
    for kind, text in blocks:
        if kind == "h2":
            lines += ["", f"## {text}", ""]
        elif kind == "h3":
            lines += ["", f"### {text}", ""]
        elif kind == "li":
            lines.append(f"- {text}")
        else:
            lines += [text, ""]
    write_txt(out, "\n".join(lines))


def write_docx(out: Path, title: str, blocks: list[tuple[str, str]]) -> None:
    doc = Document()
    doc.add_heading(title, level=0)
    for kind, text in blocks:
        if kind == "h2":
            doc.add_heading(text, level=1)
        elif kind == "h3":
            doc.add_heading(text, level=2)
        elif kind == "li":
            doc.add_paragraph(text, style="List Bullet")
        else:
            doc.add_paragraph(text)
    doc.save(out)


_pdf_styles = None


def pdf_styles():
    global _pdf_styles
    if _pdf_styles is None:
        pdfmetrics.registerFont(TTFont("SimHei", FONT))
        base = dict(fontName="SimHei", wordWrap="CJK")
        _pdf_styles = {
            "title": ParagraphStyle("T", fontSize=18, leading=26, alignment=1, spaceAfter=18, **base),
            "h2": ParagraphStyle("H2", fontSize=13, leading=20, spaceBefore=12, spaceAfter=6, **base),
            "h3": ParagraphStyle("H3", fontSize=11.5, leading=18, spaceBefore=8, spaceAfter=4, **base),
            "body": ParagraphStyle("B", fontSize=10.5, leading=17, spaceAfter=5, **base),
        }
    return _pdf_styles


def _pdf_flow(title: str, blocks: list[tuple[str, str]]):
    st = pdf_styles()
    story = [Paragraph(title, st["title"])]
    for kind, text in blocks:
        if kind == "h2":
            story += [Paragraph(text, st["h2"])]
        elif kind == "h3":
            story += [Paragraph(text, st["h3"])]
        else:
            story += [Paragraph(text, st["body"]), Spacer(1, 3)]
    return story


def write_pdf(out: Path, title: str, blocks: list[tuple[str, str]]) -> None:
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=2.2 * cm, rightMargin=2.2 * cm, topMargin=2 * cm, bottomMargin=2 * cm)
    doc.build(_pdf_flow(title, blocks))


def flatten(blocks: list[tuple[str, str]], skip_h2: re.Pattern | None = None) -> list[tuple[str, str]]:
    """可选过滤 h2（用于筛选生平类章节）。"""
    if skip_h2 is None:
        return blocks
    out, dropping = [], False
    for kind, text in blocks:
        if kind == "h2":
            dropping = bool(skip_h2.match(text))
        if not dropping:
            out.append((kind, text))
    return out


def lead_only(blocks: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """仅取条目导语（第一个 h2 之前的内容）。"""
    out = []
    for kind, text in blocks:
        if kind == "h2":
            break
        out.append((kind, text))
    return out


def body_without_headings(blocks: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """去掉章节标题，保留段落/列表（用于汇编文档正文）。"""
    return [(k, t) for k, t in blocks if k in ("p", "li")]


# ---------- 主流程 ----------


def main() -> None:
    wiki_hanwudi = KB / "html" / "维基百科-汉武帝.html"
    wiki_tuien = KB / "html" / "维基百科-推恩令.html"
    wiki_hanxiong = KB / "html" / "维基百科-汉匈战争.html"

    # ---- TXT（史料原文 + 年表） ----
    shiji = wikisource_text(RAW / "史记卷12孝武本纪.html")
    write_txt(KB / "txt" / "史记·孝武本纪（原文）.txt", "孝武本纪第十二\n\n" + shiji)
    hanshu = wikisource_text(RAW / "汉书卷06武帝纪.html")
    write_txt(KB / "txt" / "汉书·武帝纪（原文）.txt", "武帝纪第六\n\n" + hanshu)

    # ---- MD ----
    blocks_hw = wiki_blocks(wiki_hanwudi)
    SKIP_FAMILY = re.compile(r"^(家庭|后妃|子女|评价|影響|影响|形象|纪念|艺术|世系|年表|参见|参考|注)")
    write_markdown(
        KB / "md" / "汉武帝生平概述.md",
        "汉武帝生平概述",
        lead_only(blocks_hw) + flatten(blocks_hw[len(lead_only(blocks_hw)):], SKIP_FAMILY),
    )
    write_markdown(KB / "md" / "推恩令专题解析.md", "推恩令专题解析", wiki_blocks(wiki_tuien))
    write_markdown(KB / "md" / "罢黜百家独尊儒术专题.md", "罢黜百家，独尊儒术专题", wiki_blocks(RAW / "罢黜百家独尊儒术.html"))

    # ---- DOCX ----
    write_docx(KB / "docx" / "维基百科·汉武帝.docx", "维基百科：汉武帝", wiki_blocks(wiki_hanwudi, cap=20000))
    wei = wiki_blocks(RAW / "卫青.html", cap=6000)
    huo = wiki_blocks(RAW / "霍去病.html", cap=6000)
    hanxiong_lead = lead_only(wiki_blocks(wiki_hanxiong, cap=1500))
    write_docx(
        KB / "docx" / "卫青与霍去病.docx",
        "卫青与霍去病：汉匈战争中的名将",
        [("p", "编者按：本文汇编自维基百科「汉匈战争」「卫青」「霍去病」条目相关内容。")]
        + [("h2", "背景：汉匈战争"), *[b for b in hanxiong_lead if b[0] == "p"]]
        + [("h2", "卫青"), *body_without_headings(wei)]
        + [("h2", "霍去病"), *body_without_headings(huo)],
    )
    write_docx(KB / "docx" / "盐铁专卖与均输平准.docx", "盐铁专卖与均输平准：汉武帝的经济政策", wiki_blocks(RAW / "盐铁专卖.html"))

    # ---- PDF ----
    folklore = folklore_text()
    folk_blocks = []
    for para in folklore.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        if re.match(r"^[一二三四五六七八九十]+、", para):
            folk_blocks.append(("h2", para.splitlines()[0][:40]))
            folk_blocks.append(("p", "\n".join(para.splitlines()[1:]) or para))
        else:
            folk_blocks.append(("p", para))
    write_pdf(KB / "pdf" / "汉武帝：从历史人物到小说形象（黄景春）.pdf", "汉武帝：从历史人物到小说形象", [("p", "作者：黄景春（中国民俗学网）")] + folk_blocks)

    compile_intro = ("p", "编者按：本文档汇编自维基百科「推恩令」「罢黜百家，独尊儒术」「盐铁专卖」条目的核心内容，"
                         "梳理汉武帝为巩固大一统王朝在政治、思想、经济三方面采取的措施。")
    tuien_b = body_without_headings(wiki_blocks(wiki_tuien, cap=4200))
    bachu_b = body_without_headings(wiki_blocks(RAW / "罢黜百家独尊儒术.html", cap=4200))
    yantie_b = body_without_headings(wiki_blocks(RAW / "盐铁专卖.html", cap=4200))
    write_pdf(
        KB / "pdf" / "汉武帝巩固大一统的措施解析.pdf",
        "汉武帝巩固大一统的措施解析",
        [compile_intro, ("h2", "一、政治：推恩令与削弱诸侯"), *tuien_b,
         ("h2", "二、思想：罢黜百家，独尊儒术"), *bachu_b,
         ("h2", "三、经济：盐铁专卖与国家专营"), *yantie_b],
    )

    zhangqian = wiki_blocks(RAW / "张骞.html", cap=12000)
    write_pdf(KB / "pdf" / "张骞出使西域与丝绸之路.pdf", "张骞出使西域与丝绸之路", zhangqian)

    # ---- 汇总 ----
    for sub in ("pdf", "docx", "txt", "md", "html"):
        files = sorted((KB / sub).glob("*"))
        for f in files:
            print(f"{sub}/{f.name}  {f.stat().st_size} bytes")


if __name__ == "__main__":
    main()
