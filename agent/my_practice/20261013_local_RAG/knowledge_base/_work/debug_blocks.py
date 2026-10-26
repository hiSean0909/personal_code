# -*- coding: utf-8 -*-
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from collect_docs import wiki_blocks, wiki_title, KB, RAW  # noqa: E402

for p, name in [
    (KB / "html" / "维基百科-汉武帝.html", "汉武帝"),
    (RAW / "桑弘羊.html", "桑弘羊"),
    (RAW / "丝绸之路.html", "丝绸之路"),
]:
    try:
        blocks = wiki_blocks(p)
        chars = sum(len(t) for _, t in blocks)
        h2s = [t for k, t in blocks if k == "h2"][:14]
        h3s = [t for k, t in blocks if k == "h3"][:30]
        print(f"{name}: {len(blocks)} blocks, {chars} chars, title={wiki_title(p)}")
        print(f"  h2: {h2s}")
        print(f"  h3: {h3s}")
    except Exception as e:
        print(f"{name}: ERROR {e}")
