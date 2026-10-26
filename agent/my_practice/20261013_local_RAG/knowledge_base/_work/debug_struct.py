# -*- coding: utf-8 -*-
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from collect_docs import soup_of, KB, RAW  # noqa: E402

for p, name in [(KB / "html" / "维基百科-汉武帝.html", "汉武帝"), (RAW / "张骞.html", "张骞")]:
    soup = soup_of(p)
    print(f"===== {name} =====")
    root = soup.select_one(".mw-parser-output")
    print("has mw-parser-output:", root is not None)
    if root is None:
        # 找出正文容器候选
        for sel in ["#mw-content-text", ".mw-content", "#content", ".mw-page-container-main"]:
            el = soup.select_one(sel)
            print(f"  {sel}: {el is not None}", end="")
            if el is not None:
                print(f" text={len(el.get_text(strip=True))}")
            else:
                print()
        continue
    print("root text chars:", len(root.get_text(strip=True)))
    kids = {}
    for c in root.find_all(True, recursive=False):
        kids[c.name] = kids.get(c.name, 0) + 1
    print("direct children:", kids)
    total = root.find_all(["h2", "h3", "p", "ul", "ol"])
    print("all p/h2/h3/ul/ol:", len(total))
    first_p = root.find("p")
    print("first p text:", (first_p.get_text(strip=True)[:80] if first_p else None))
