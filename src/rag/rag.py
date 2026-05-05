"""
主 RAG 协调器：组装所有模块，对外提供统一接口
"""
import sys
from typing import List, Tuple, Generator

from langchain_openai import ChatOpenAI
from chromadb.utils import embedding_functions

from .config import GeneralConfig, DEEPSEEK_MODEL, DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL
from .cache import LLMCache
from .query_transformer import QueryTransformer
from .processor import ParagraphSemanticProcessor
from .retriever import GeneralHybridRetriever
from .generator import GeneralGenerator


class GeneralTerminalRAG:
    """RAG 系统总控：初始化 → 加载文档 → 构建索引 → 对话就绪"""

    def __init__(self, config: GeneralConfig | None = None):
        self.config = config or GeneralConfig()

        print("正在初始化大模型（DeepSeek）...")
        self.llm = ChatOpenAI(
            model=DEEPSEEK_MODEL,
            openai_api_key=DEEPSEEK_API_KEY,
            openai_api_base=DEEPSEEK_BASE_URL,
            temperature=0,
            timeout=120,
            max_tokens=2048,
        )
        self.query_transformer = QueryTransformer(self.config, self.llm)
        self.embedding_model = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.config.EMBEDDING_MODEL, device="cpu",
        )
        self.processor = ParagraphSemanticProcessor(self.config)
        self.retriever = GeneralHybridRetriever(
            self.config, self.embedding_model, self.query_transformer)
        self.generator = GeneralGenerator(self.llm)
        self.cache = LLMCache(self.config.LLM_CACHE_FILE)
        self.conversation_history: List[Tuple[str, str]] = []

        print("正在加载和处理文档...")
        self.documents = self.processor.load_documents(self.config.DOCS_DIR)
        print(f"  [加载] 原始文档数: {len(self.documents)}", flush=True)
        self.splits = self.processor.split_documents(self.documents)
        print(f"  [分块] 文本块数: {len(self.splits)}", flush=True)
        if self.splits:
            print(f"  [分块] 大小: {min(len(s.page_content) for s in self.splits)}"
                  f"~{max(len(s.page_content) for s in self.splits)} 字符",
                  flush=True)
        self.retriever.build_indexes(self.splits)
        print("=" * 60)
        print("RAG 系统初始化完成（DeepSeek）！")
        print("=" * 60)

    def ask(self, query: str) -> str:
        sys.stderr.write(f"[ASK] {query[:60]}\n"); sys.stderr.flush()
        if self.config.ENABLE_LLM_CACHE:
            cached = self.cache.get(query)
            if cached:
                return cached
        contextualized = self.query_transformer.contextualize_query(
            query, self.conversation_history)
        sys.stderr.write(
            f"[ASK] ctx: {contextualized[:80]}\n"); sys.stderr.flush()
        retrieved = self.retriever.invoke(contextualized)
        sys.stderr.write(f"[ASK] hits: {len(retrieved)}\n"); sys.stderr.flush()
        answer = self.generator.generate(contextualized, retrieved)
        self.add_to_history(query, answer)
        if self.config.ENABLE_LLM_CACHE:
            self.cache.set(query, answer)
        return answer

    def ask_stream(self, query: str) -> Generator[str, None, None]:
        sys.stderr.write(f"[STREAM] {query[:60]}\n"); sys.stderr.flush()
        contextualized = self.query_transformer.contextualize_query(
            query, self.conversation_history)
        sys.stderr.write(
            f"[STREAM] ctx: {contextualized[:80]}\n"); sys.stderr.flush()
        retrieved = self.retriever.invoke(contextualized)
        sys.stderr.write(
            f"[STREAM] hits: {len(retrieved)}\n"); sys.stderr.flush()
        full_answer = ""
        for token in self.generator.generate_stream(
                query, retrieved, self.conversation_history):
            full_answer += token
            yield token
        self.add_to_history(query, full_answer)

    def add_to_history(self, question: str, answer: str):
        self.conversation_history.append((question, answer))
        if len(self.conversation_history) > self.config.MAX_CONVERSATION_TURNS:
            self.conversation_history = (
                self.conversation_history[-self.config.MAX_CONVERSATION_TURNS:])

    def clear_history(self):
        self.conversation_history = []

    def run(self):
        print("\n请输入你的问题（输入 'quit' 或 'exit' 退出）：")
        while True:
            try:
                ui = input("\n你的问题：").strip()
                if ui.lower() in ("quit", "exit", "退出"):
                    print("再见！"); break
                if not ui:
                    print("请输入有效的问题！"); continue
                if self.config.ENABLE_LLM_CACHE:
                    cached = self.cache.get(ui)
                    if cached:
                        print("\n系统回答（缓存命中）：")
                        print("-" * 60); print(cached); print("-" * 60)
                        continue
                print("正在检索和思考...")
                contextualized = self.query_transformer.contextualize_query(
                    ui, self.conversation_history)
                retrieved = self.retriever.invoke(contextualized)
                answer = self.generator.generate(contextualized, retrieved)
                self.add_to_history(ui, answer)
                if self.config.ENABLE_LLM_CACHE:
                    self.cache.set(ui, answer)
                print("\n系统回答：")
                print("-" * 60); print(answer); print("-" * 60)
            except KeyboardInterrupt:
                print("\n再见！"); break
            except Exception as e:
                print(f"处理失败：{e}")
