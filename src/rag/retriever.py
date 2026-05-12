"""
混合检索：BM25 关键词 + ChromaDB 语义 + Reranker 精排
"""
import os
import sys
import hashlib
import shutil
from typing import List

import chromadb
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from sentence_transformers import CrossEncoder

from .config import GeneralConfig
from .query_transformer import QueryTransformer


class GeneralHybridRetriever:
    """BM25 + ChromaDB 双路混合检索"""

    def __init__(self, config: GeneralConfig,
                 embedding_model,
                 query_transformer: QueryTransformer):
        self.config = config
        self.embedding_model = embedding_model
        self.query_transformer = query_transformer
        self.splits: List[Document] | None = None
        self.bm25_retriever = None
        self.chroma_collection = None
        self.reranker: CrossEncoder | None = None
        self._init_chroma()
        self._init_reranker()

    def _init_chroma(self):
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=self.config.CHROMA_DIR)
            self.chroma_collection = self.chroma_client.get_or_create_collection(
                name="general_rag",
                embedding_function=self.embedding_model,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception:
            if os.path.exists(self.config.CHROMA_DIR):
                shutil.rmtree(self.config.CHROMA_DIR)
            os.makedirs(self.config.CHROMA_DIR, exist_ok=True)
            self.chroma_client = chromadb.PersistentClient(
                path=self.config.CHROMA_DIR)
            self.chroma_collection = self.chroma_client.get_or_create_collection(
                name="general_rag",
                embedding_function=self.embedding_model,
                metadata={"hnsw:space": "cosine"},
            )

    def _init_reranker(self):
        self.reranker = CrossEncoder(
            self.config.RERANKER_MODEL, device="cpu")

    def build_indexes(self, splits: List[Document]):
        if not splits:
            raise ValueError("没有可构建索引的文本块")
        self.splits = splits
        self.bm25_retriever = BM25Retriever.from_documents(splits)
        self.bm25_retriever.k = self.config.BM25_K
        if self.chroma_collection.count() == 0:
            texts = [d.page_content for d in splits]
            metas = [d.metadata for d in splits]
            ids = [f"doc_{i}" for i in range(len(splits))]
            batch = 100
            for i in range(0, len(texts), batch):
                self.chroma_collection.add(
                    documents=texts[i:i + batch],
                    metadatas=metas[i:i + batch],
                    ids=ids[i:i + batch],
                )

    def _bm25_search(self, query: str) -> List[Document]:
        return self.bm25_retriever.invoke(query)

    def _semantic_search(self, query: str) -> List[Document]:
        res = self.chroma_collection.query(
            query_texts=[query],
            n_results=self.config.SEMANTIC_K,
        )
        docs = []
        for i in range(len(res["documents"][0])):
            docs.append(Document(
                page_content=res["documents"][0][i],
                metadata=res["metadatas"][0][i],
            ))
        return docs

    def _rerank(self, query: str, docs: List[Document]) -> List[Document]:
        if not docs:
            return []
        unique = []
        seen = set()
        for d in docs:
            h = hashlib.md5(d.page_content.encode()).hexdigest()
            if h not in seen:
                seen.add(h); unique.append(d)
        pairs = [[query, d.page_content] for d in unique]
        scores = self.reranker.predict(pairs)
        sys.stderr.write(
            f"[RERANK] {len(unique)} docs, "
            f"range: {min(scores):.4f}~{max(scores):.4f}\n"
        ); sys.stderr.flush()
        scored = list(zip(unique, scores))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [d for d, _ in scored[:self.config.RERANK_TOP_K]]

    def invoke(self, original_query: str,
               mode: str | None = None,
               enable_rerank: bool | None = None,
               rerank_top_k: int | None = None) -> List[Document]:
        """混合检索入口，支持运行时覆盖检索策略"""
        _mode = mode or self.config.RETRIEVAL_MODE
        _rerank = enable_rerank if enable_rerank is not None else self.config.ENABLE_RERANK
        _top_k = rerank_top_k or self.config.RERANK_TOP_K

        # 查询改写
        if self.config.ENABLE_QUERY_REWRITE:
            rewritten = self.query_transformer.rewrite_query(original_query)
            sys.stderr.write(f"[RETR] rewrite: {rewritten[:60]}\n")
            sys.stderr.flush()
        else:
            rewritten = original_query

        # 多查询生成
        if self.config.ENABLE_MULTI_QUERY:
            queries = self.query_transformer.generate_multi_queries(rewritten)
            sys.stderr.write(f"[RETR] {len(queries)} variants\n")
            sys.stderr.flush()
        else:
            queries = [rewritten]

        # 双路检索
        all_docs: List[Document] = []
        for q in queries:
            if _mode in ("bm25", "hybrid"):
                bm25 = self._bm25_search(q)
            else:
                bm25 = []
            if _mode in ("semantic", "hybrid"):
                sem = self._semantic_search(q)
            else:
                sem = []
            sys.stderr.write(
                f"[RETR]   q='{q[:40]}' bm25={len(bm25)} sem={len(sem)}\n"
            ); sys.stderr.flush()
            all_docs.extend(bm25 + sem)

        sys.stderr.write(f"[RETR] pre-dedup: {len(all_docs)}\n")
        sys.stderr.flush()

        # 去重
        unique = []
        seen = set()
        for d in all_docs:
            h = hashlib.md5(d.page_content.encode()).hexdigest()
            if h not in seen:
                seen.add(h); unique.append(d)

        # 重排序
        if _rerank:
            unique = self._rerank(rewritten, unique)
            sys.stderr.write(
                f"[RETR] reranked → top-{_top_k}: {min(len(unique), _top_k)}\n"
            ); sys.stderr.flush()
            return unique[:_top_k]

        sys.stderr.write(
            f"[RETR] top-{_top_k}: {min(len(unique), _top_k)}\n"
        ); sys.stderr.flush()
        return unique[:_top_k]
