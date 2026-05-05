"""
LLM 回答缓存
"""
import os
import pickle
import hashlib
from typing import Dict


class LLMCache:
    """基于 MD5 哈希的查询-回答缓存"""

    def __init__(self, cache_file: str):
        self.cache_file = cache_file
        self.cache: Dict[str, str] = self._load_cache()

    def _load_cache(self) -> Dict[str, str]:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "rb") as f:
                    return pickle.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self):
        with open(self.cache_file, "wb") as f:
            pickle.dump(self.cache, f)

    def get(self, query: str) -> str | None:
        query_hash = hashlib.md5(query.strip().lower().encode()).hexdigest()
        return self.cache.get(query_hash)

    def set(self, query: str, answer: str):
        query_hash = hashlib.md5(query.strip().lower().encode()).hexdigest()
        self.cache[query_hash] = answer
        self._save_cache()
