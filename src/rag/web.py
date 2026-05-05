"""
Flask Web 前端：SSE 流式 + 多轮对话 + 冰蓝档案主题 + 多对话管理
"""
import os
import sys
import json as _json
import glob

from flask import Flask, request, jsonify, render_template_string, Response

from .templates import WEB_HTML
from .rag import GeneralTerminalRAG
from .config import GeneralConfig


def _build_snippets(rag, query):
    """辅助：检索并构建 snippets"""
    contextualized = rag.query_transformer.contextualize_query(
        query, rag.conversation_history)
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
    return snippets[:6]


def _apply_conv_history(rag, conv_id: str):
    """从对话存储加载历史到 RAG 系统"""
    history = rag.conv_store.get_history_for_rag(conv_id, rag.config.MAX_CONVERSATION_TURNS)
    rag.conversation_history = history


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

    # ═══════════════════════════════════════════
    #  对话 CRUD
    # ═══════════════════════════════════════════

    @app.route("/api/conversations", methods=["GET"])
    def api_list_conversations():
        convs = rag.conv_store.list_conversations()
        return jsonify({"conversations": convs})

    @app.route("/api/conversations", methods=["POST"])
    def api_create_conversation():
        data = request.get_json() or {}
        title = data.get("title", "新对话")
        conv = rag.conv_store.create_conversation(title)
        return jsonify({"conversation": conv})

    @app.route("/api/conversations/<conv_id>", methods=["GET"])
    def api_get_conversation(conv_id):
        conv = rag.conv_store.get_conversation(conv_id)
        if not conv:
            return jsonify({"error": "对话不存在"}), 404
        return jsonify({"conversation": conv})

    @app.route("/api/conversations/<conv_id>", methods=["DELETE"])
    def api_delete_conversation(conv_id):
        ok = rag.conv_store.delete_conversation(conv_id)
        if not ok:
            return jsonify({"error": "对话不存在"}), 404
        return jsonify({"status": "ok"})

    @app.route("/api/conversations/<conv_id>/rename", methods=["POST"])
    def api_rename_conversation(conv_id):
        data = request.get_json() or {}
        title = data.get("title", "").strip()
        if not title:
            return jsonify({"error": "标题不能为空"}), 400
        rag.conv_store.rename_conversation(conv_id, title)
        return jsonify({"status": "ok"})

    # ═══════════════════════════════════════════
    #  问答（支持对话 ID）
    # ═══════════════════════════════════════════

    @app.route("/api/ask", methods=["POST"])
    def api_ask():
        data = request.get_json()
        query = data.get("query", "").strip()
        conv_id = data.get("conversation_id", "")
        if not query:
            return jsonify({"error": "问题不能为空"}), 400
        if len(query) > 2000:
            return jsonify({"error": "问题长度超过限制"}), 400
        try:
            if conv_id:
                _apply_conv_history(rag, conv_id)
            answer = rag.ask(query)
            if conv_id:
                rag.conv_store.add_message(conv_id, "user", query)
                rag.conv_store.add_message(conv_id, "assistant", answer)
            snippets = _build_snippets(rag, query)
            return jsonify({
                "answer": answer,
                "snippets": snippets,
            })
        except Exception as e:
            return jsonify({"error": f"生成回答失败：{str(e)}"}), 500

    @app.route("/api/ask/stream", methods=["POST"])
    def api_ask_stream():
        data = request.get_json()
        query = data.get("query", "").strip()
        conv_id = data.get("conversation_id", "")
        if not query:
            return jsonify({"error": "问题不能为空"}), 400
        if len(query) > 2000:
            return jsonify({"error": "问题长度超过限制"}), 400

        def generate():
            try:
                if conv_id:
                    _apply_conv_history(rag, conv_id)
                    rag.conv_store.add_message(conv_id, "user", query)

                contextualized = rag.query_transformer.contextualize_query(
                    query, rag.conversation_history,
                )
                retrieved = rag.retriever.invoke(contextualized)
                snippets = _build_snippets(rag, query)
                sys.stderr.write(
                    f"[SSE] retrieval: {len(retrieved)} docs, "
                    f"{len(snippets)} snippets\n"
                ); sys.stderr.flush()
                yield (
                    "data: " + _json.dumps(
                        {"type": "retrieval_done", "snippets": snippets},
                        ensure_ascii=False,
                    ) + "\n\n"
                )

                full_answer = ""
                for token in rag.ask_stream(query):
                    full_answer += token
                    yield (
                        "data: " + _json.dumps(
                            {"type": "token", "text": token},
                            ensure_ascii=False,
                        ) + "\n\n"
                    )

                if conv_id:
                    rag.conv_store.add_message(conv_id, "assistant", full_answer)

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

    # ═══════════════════════════════════════════
    #  兼容旧 API
    # ═══════════════════════════════════════════

    @app.route("/api/conversation/clear", methods=["POST"])
    def api_clear_conversation():
        rag.clear_history()
        return jsonify({"status": "ok"})

    @app.route("/api/conversation/history")
    def api_conversation_history():
        history = [{"q": q, "a": a} for q, a in rag.conversation_history]
        return jsonify({"history": history})

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
    print(f"  ★ 多对话管理已启用")
    print(f"{'=' * 60}\n")
    app.run(host=host, port=port, debug=False, threaded=True)
