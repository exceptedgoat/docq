"""
一次性脚本：从 rag_new_v2.py 中提取 WEB_HTML 常量 → _templates.py
运行一次即可：
    python src/rag/extract_templates.py
"""
import re
import os

SRC = os.path.join(os.path.dirname(__file__), "..", "..", "rag_new_v2.py")
DST = os.path.join(os.path.dirname(__file__), "_templates.py")

with open(SRC, "r", encoding="utf-8") as f:
    content = f.read()

# 匹配 WEB_HTML = r"""...""" 直到下一个顶层 def
pattern = r'WEB_HTML = r(""".+?""")\s*\ndef create_web_app'
match = re.search(pattern, content, re.DOTALL)
if not match:
    print("ERROR: 未找到 WEB_HTML 常量")
    exit(1)

html_literal = match.group(1)  # 包含 r""" 和 """
with open(DST, "w", encoding="utf-8") as f:
    f.write(f'"""Glacial Archive 前端模板 (自动提取)"""\n')
    f.write(f'WEB_HTML = r{html_literal}\n')

print(f"提取成功: {DST}  ({len(html_literal)} 字符)")
