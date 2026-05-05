"""
多对话管理：文件持久化，支持新建/切换/删除会话
"""
import json
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional

# 北京时间
TZ = timezone(timedelta(hours=8))


def _now() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def _short_id() -> str:
    return uuid.uuid4().hex[:8]


class ConversationStore:
    """管理多个对话，每个对话存为独立的 JSON 文件"""

    def __init__(self, store_dir: str):
        self.store_dir = store_dir
        os.makedirs(store_dir, exist_ok=True)
        self._active_id: Optional[str] = None
        self._active_messages: List[Dict] = []

    # ── 文件路径 ──
    def _path(self, conv_id: str) -> str:
        return os.path.join(self.store_dir, f"{conv_id}.json")

    # ── 加载/保存单条对话 ──
    def _load(self, conv_id: str) -> Optional[Dict]:
        p = self._path(conv_id)
        if not os.path.exists(p):
            return None
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, conv: Dict):
        conv["updated_at"] = _now()
        with open(self._path(conv["id"]), "w", encoding="utf-8") as f:
            json.dump(conv, f, ensure_ascii=False, indent=2)

    # ── 公开 API ──

    def list_conversations(self) -> List[Dict]:
        """返回所有对话摘要（不含完整消息）"""
        result = []
        for fn in sorted(os.listdir(self.store_dir), reverse=True):
            if not fn.endswith(".json"):
                continue
            try:
                p = os.path.join(self.store_dir, fn)
                with open(p, "r", encoding="utf-8") as f:
                    conv = json.load(f)
            except Exception:
                continue
            msgs = conv.get("messages", [])
            preview = ""
            for m in msgs:
                if m["role"] == "user":
                    preview = m["content"][:60]
                    break
            result.append({
                "id": conv["id"],
                "title": conv.get("title", "新对话"),
                "created_at": conv.get("created_at", ""),
                "updated_at": conv.get("updated_at", ""),
                "message_count": len(msgs),
                "preview": preview,
            })
        return result

    def get_conversation(self, conv_id: str) -> Optional[Dict]:
        return self._load(conv_id)

    def create_conversation(self, title: str = "新对话") -> Dict:
        conv = {
            "id": f"{datetime.now(TZ).strftime('%Y%m%d')}-{_short_id()}",
            "title": title,
            "created_at": _now(),
            "updated_at": _now(),
            "messages": [],
        }
        self._save(conv)
        return conv

    def delete_conversation(self, conv_id: str) -> bool:
        p = self._path(conv_id)
        if os.path.exists(p):
            os.remove(p)
            if self._active_id == conv_id:
                self._active_id = None
                self._active_messages = []
            return True
        return False

    def add_message(self, conv_id: str, role: str, content: str):
        conv = self._load(conv_id)
        if not conv:
            return
        conv["messages"].append({
            "role": role,
            "content": content,
            "timestamp": _now(),
        })
        # 第一条用户消息自动作为标题
        if role == "user" and conv.get("title") == "新对话":
            conv["title"] = content[:30]
        self._save(conv)

    def get_history_for_rag(self, conv_id: str, max_turns: int = 6) -> List[tuple]:
        """提取最近 N 轮 Q&A，返回 [(q, a), ...] 格式供 RAG 使用"""
        conv = self._load(conv_id)
        if not conv:
            return []
        qa_pairs = []
        buf_q = None
        for m in conv.get("messages", []):
            if m["role"] == "user":
                buf_q = m["content"]
            elif m["role"] == "assistant" and buf_q is not None:
                qa_pairs.append((buf_q, m["content"]))
                buf_q = None
        return qa_pairs[-max_turns:]

    def rename_conversation(self, conv_id: str, title: str):
        conv = self._load(conv_id)
        if conv:
            conv["title"] = title
            self._save(conv)
