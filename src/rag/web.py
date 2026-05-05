"""
Flask Web 前端：SSE 流式 + 多轮对话 + 冰蓝档案主题
"""
import os
import sys
import json as _json
import glob

from flask import Flask, request, jsonify, render_template_string, Response

from .templates import WEB_HTML
from .rag import GeneralTerminalRAG
from .config import GeneralConfig


def create_web_app(rag: GeneralTerminalRAG) -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template_string(WEB_HTML)

    @app.route("/api/files")
    def api_files():
        files = []
        for ext in rag.config.SUPPORTED_EXTENSIONS:
            for f in glob.glob(
                os.path.join(rag.config.DOCS_DIR, f"*{ext}")
            ):
                files.append(os.path.basename(f))
        return jsonify({"files": files[:20]})

    @app.route("/api/ask", methods=["POST"])
    def api_ask():
        data = request.get_json()
        query = data.get("query", "").strip()
        if not query:
            return jsonify({"error": "问题不能为空"}), 400
        if len(query) > 2000:
            return jsonify({"error": "问题长度超过限制"}), 400
        try:
            answer = rag.ask(query)
            retrieved = rag.retriever.invoke(
                rag.query_transformer.contextualize_query(
                    query, rag.conversation_history[:-1]
                )
            )
            sources = []
            snippets = []
            seen_files = set()
            seen_texts = set()
            for doc in retrieved[:8]:
                fname = doc.metadata.get("file_name", "未知文档")
                text = doc.page_content.strip()
                if fname not in seen_files:
                    seen_files.add(fname)
                    sources.append(fname)
                text_key = text[:80]
                if text_key not in seen_texts and len(text) >= 10:
                    seen_texts.add(text_key)
                    snippets.append({"file": fname, "text": text[:600]})
            return jsonify({
                "answer": answer,
                "sources": sources,
                "snippets": snippets[:6],
            })
        except Exception as e:
            return jsonify({"error": f"生成回答失败：{str(e)}"}), 500

    @app.route("/api/ask/stream", methods=["POST"])
    def api_ask_stream():
        data = request.get_json()
        query = data.get("query", "").strip()
        if not query:
            return jsonify({"error": "问题不能为空"}), 400
        if len(query) > 2000:
            return jsonify({"error": "问题长度超过限制"}), 400

        def generate():
            try:
                contextualized = rag.query_transformer.contextualize_query(
                    query, rag.conversation_history,
                )
                retrieved = rag.retriever.invoke(contextualized)
                snippets = []
                seen_files = set()
                seen_texts = set()
                for doc in retrieved[:8]:
                    fname = doc.metadata.get("file_name", "未知文档")
                    text = doc.page_content.strip()
                    if fname not in seen_files:
                        seen_files.add(fname)
                    text_key = text[:80]
                    if text_key not in seen_texts and len(text) >= 10:
                        seen_texts.add(text_key)
                        snippets.append({"file": fname, "text": text[:600]})
                sys.stderr.write(
                    f"[SSE] retrieval: {len(retrieved)} docs, "
                    f"{len(snippets[:6])} snippets\n"
                ); sys.stderr.flush()
                yield (
                    "data: " + _json.dumps(
                        {"type": "retrieval_done", "snippets": snippets[:6]},
                        ensure_ascii=False,
                    ) + "\n\n"
                )

                for token in rag.ask_stream(query):
                    yield (
                        "data: " + _json.dumps(
                            {"type": "token", "text": token},
                            ensure_ascii=False,
                        ) + "\n\n"
                    )

                yield (
                    "data: " + _json.dumps(
                        {"type": "done"}, ensure_ascii=False,
                    ) + "\n\n"
                )
            except Exception as e:
                import traceback
                traceback.print_exc(file=sys.stderr)
                yield (
                    "data: " + _json.dumps(
                        {"type": "error", "message": str(e)},
                        ensure_ascii=False,
                    ) + "\n\n"
                )

        return Response(
            generate(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    @app.route("/api/conversation/clear", methods=["POST"])
    def api_clear_conversation():
        rag.clear_history()
        return jsonify({"status": "ok"})

    return app


def run_web(host="0.0.0.0", port=7860):
    try:
        from flask import Flask  # noqa: F811
    except ImportError:
        print("[错误] 缺少 Flask，请执行: pip install flask --break-system-packages")
        return
    print("正在启动 Web 前端...")
    config = GeneralConfig()
    rag = GeneralTerminalRAG(config)
    app = create_web_app(rag)
    print(f"\n{'=' * 60}")
    print(f"  DocQ Web 前端已就绪")
    print(f"  打开浏览器访问: http://localhost:{port}")
    print(f"  ★ SSE 流式输出已启用")
    print(f"  ★ 多轮对话已启用 (最多{config.MAX_CONVERSATION_TURNS}轮)")
    print(f"{'=' * 60}\n")
    app.run(host=host, port=port, debug=False, threaded=True)
