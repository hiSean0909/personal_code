import re

p = r"d:\personal\git\personal_code\agent\my_practice\20261013_local_RAG\knowledge_base\_work\raw\folklore_p2.html"
raw = open(p, "rb").read()
print("bytes:", len(raw))
print("first 300 raw bytes:", raw[:300])
for enc in ("utf-8", "gb18030"):
    try:
        s = raw.decode(enc)
        print(f"--- decoded as {enc}, {len(s)} chars ---")
        idx = s.find("继续浏览")
        print("has 继续浏览 at", idx)
        # strip tags, show text
        txt = re.sub(r"<script.*?</script>", " ", s, flags=re.S)
        txt = re.sub(r"<[^>]+>", " ", txt)
        txt = re.sub(r"\s+", " ", txt)
        print("total plain chars:", len(txt))
        print(txt[:600])
        break
    except Exception as e:
        print(enc, "failed:", e)
