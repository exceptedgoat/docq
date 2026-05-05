"""前端 HTML 模板（需先运行 extract_templates.py 生成）"""
try:
    from ._templates import WEB_HTML
except ImportError:
    WEB_HTML = "<html><body><p>请先运行 python src/rag/extract_templates.py</p></body></html>"
