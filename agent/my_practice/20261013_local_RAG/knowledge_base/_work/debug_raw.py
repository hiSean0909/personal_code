# -*- coding: utf-8 -*-
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from collect_docs import soup_of, KB  # noqa: E402

soup = soup_of(KB / "html" / "维基百科-汉武帝.html")
raw = (KB / "html" / "维基百科-汉武帝.html").read_bytes()
print("raw bytes:", len(raw))
print("contains 刘彻:", raw.count("刘彻".encode()), "contains 孝武:", raw.count("孝武".encode()))

# 找出文本最多的元素
best = []
for tag in soup.find_all(True):
    t = tag.get_text(" ", strip=True)
    best.append((len(t), tag.name, str(tag.get("class"))[:60]))
best.sort(key=lambda x: -x[0])
print("top text elements:")
for b in best[:10]:
    print("  ", b)

# span.mw-parser-output 附近结构
span = soup.select_one(".mw-parser-output > span")
if span is not None:
    print("the span:", str(span)[:300])
