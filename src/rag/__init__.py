"""
RAG 系统模块化版本
用法:
    python -m src.rag.main          # 终端模式
    python -m src.rag.main web      # Web 模式
"""

from .config import GeneralConfig
from .cache import LLMCache
from .query_transformer import QueryTransformer
from .processor import ParagraphSemanticProcessor
from .retriever import GeneralHybridRetriever
from .generator import GeneralGenerator
from .rag import GeneralTerminalRAG
from .conversation_store import ConversationStore
from .evaluate import RAGEvaluator, EvalResult, ExperimentReport
from .experiment import (
    RAGExperimentRunner, ComparisonReport, ExperimentDef,
    PRESET_GROUPS,
    preset_retrieval_strategies, preset_top_k,
    preset_query_optimizations, preset_all,
)

__all__ = [
    "GeneralConfig",
    "LLMCache",
    "QueryTransformer",
    "ParagraphSemanticProcessor",
    "GeneralHybridRetriever",
    "GeneralGenerator",
    "GeneralTerminalRAG",
    "ConversationStore",
    "RAGEvaluator",
    "EvalResult",
    "ExperimentReport",
    "RAGExperimentRunner",
    "ComparisonReport",
    "ExperimentDef",
    "PRESET_GROUPS",
]
