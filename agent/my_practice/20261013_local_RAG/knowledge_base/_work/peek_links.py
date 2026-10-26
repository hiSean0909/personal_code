import re

p = r"d:\personal\git\personal_code\agent\my_practice\20261013_local_RAG\knowledge_base\_work\raw\汉武帝从历史人物到小说形象.html"
raw = open(p, "rb").read().decode("gb2312", errors="ignore")
idx = raw.find("继续浏览")
print("--- around pagination ---")
print(raw[idx - 200 : idx + 800])
print("--- any href with page ---")
for m in re.findall(r'href="([^"]*[Pp]age[^"]*)"', raw)[:10]:
    print(m)
