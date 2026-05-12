"""
全局配置
"""
import os
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_MODEL    = os.getenv("OPENAI_MODEL", "deepseek-chat")
DEEPSEEK_API_KEY  = os.getenv("OPENAI_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")


class GeneralConfig:
    """RAG 系统全局配置"""

    DOCS_DIR       = "./docs"
    CACHE_DIR      = "./cache"
    CHROMA_DIR     = "./chroma_db"
    LLM_CACHE_FILE = "./llm_cache.pkl"
    HISTORY_FILE   = "./conversation_history.json"
    CONVERSATIONS_DIR = "./conversations"

    SUPPORTED_EXTENSIONS = [
        ".pdf", ".txt", ".md", ".docx", ".doc",
        ".xlsx", ".xls", ".pptx", ".ppt",
    ]

    EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
    RERANKER_MODEL  = "BAAI/bge-reranker-base"

    MIN_PARAGRAPH_LENGTH         = 50
    MAX_SEMANTIC_CHUNK_SIZE      = 1200
    SEMANTIC_SIMILARITY_THRESHOLD = 0.75
    CHUNK_OVERLAP_PARAGRAPHS     = 2

    ENABLE_QUERY_REWRITE = True
    ENABLE_MULTI_QUERY   = True
    MULTI_QUERY_COUNT    = 4

    BM25_K       = 12
    SEMANTIC_K   = 12
    RERANK_TOP_K = 6

    RETRIEVAL_MODE = "hybrid"    # "bm25" | "semantic" | "hybrid"
    ENABLE_RERANK  = False       # 是否启用 CrossEncoder 重排序

    DEBUG_MODE       = False
    ENABLE_LLM_CACHE = True

    MAX_CONVERSATION_TURNS = 6

    def __init__(self):
        for dir_path in [self.CACHE_DIR, self.CHROMA_DIR]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
