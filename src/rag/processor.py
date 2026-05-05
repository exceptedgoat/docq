"""
文档处理器：全格式加载 · 段落分块 · 语义合并 · 元数据注入
"""
import os
import sys
import glob
import pickle
import hashlib
import traceback
import re
from typing import List, Dict

import numpy as np
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredExcelLoader,
    UnstructuredPowerPointLoader,
)
from chromadb.utils import embedding_functions
from sentence_transformers import util

from .config import GeneralConfig


class ParagraphSemanticProcessor:
    """段落+语义双阶段分块处理器"""

    def __init__(self, config: GeneralConfig):
        self.config = config
        self.embedding_model = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=config.EMBEDDING_MODEL,
            device="cpu",
        )

    def _get_file_hash(self, file_path: str) -> str:
        h = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        return h.hexdigest()

    def _load_single_file(self, file_path: str) -> List[Document]:
        ext = os.path.splitext(file_path)[1].lower()
        fname = os.path.basename(file_path)
        try:
            if ext == ".pdf":
                loader = PyMuPDFLoader(file_path)
            elif ext == ".txt":
                loader = TextLoader(file_path, encoding="utf-8")
            elif ext == ".md":
                loader = TextLoader(file_path, encoding="utf-8")
            elif ext in (".docx", ".doc"):
                loader = UnstructuredWordDocumentLoader(file_path)
            elif ext in (".xlsx", ".xls"):
                loader = UnstructuredExcelLoader(file_path, mode="elements")
            elif ext in (".pptx", ".ppt"):
                loader = UnstructuredPowerPointLoader(file_path)
            else:
                sys.stderr.write(f"[LOAD] {fname}: unsupported {ext}\n")
                sys.stderr.flush()
                return []
            docs = loader.load()
            for d in docs:
                d.metadata["file_name"] = fname
            return docs
        except Exception as e:
            sys.stderr.write(f"[LOAD] {fname}: {type(e).__name__}: {e}\n")
            sys.stderr.flush()
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            return []

    def load_documents(self, directory_path: str) -> List[Document]:
        abs_path = os.path.abspath(directory_path)
        sys.stderr.write(
            f"[LOAD] dir={directory_path}, abs={abs_path}, "
            f"exists={os.path.isdir(abs_path)}\n"
        ); sys.stderr.flush()
        all_docs: List[Document] = []
        for ext in self.config.SUPPORTED_EXTENSIONS:
            files = glob.glob(os.path.join(directory_path, f"*{ext}"))
            files += glob.glob(os.path.join(directory_path, f"**/*{ext}"),
                              recursive=True)
            files = list(set(files))
            if files:
                sys.stderr.write(
                    f"[LOAD] ext={ext} → {len(files)} files: "
                    f"{[os.path.basename(f) for f in files[:5]]}\n"
                ); sys.stderr.flush()
            for fp in files:
                fhash = self._get_file_hash(fp)
                cache_path = os.path.join(self.config.CACHE_DIR, f"{fhash}.pkl")
                if os.path.exists(cache_path):
                    try:
                        with open(cache_path, "rb") as f:
                            cached = pickle.load(f)
                        all_docs.extend(cached)
                        sys.stderr.write(
                            f"[LOAD]   {os.path.basename(fp)} "
                            f"← cache ({len(cached)} docs)\n"
                        ); sys.stderr.flush()
                        continue
                    except Exception as e:
                        sys.stderr.write(
                            f"[LOAD]   {os.path.basename(fp)} "
                            f"cache corrupt: {e}\n"
                        ); sys.stderr.flush()
                docs = self._load_single_file(fp)
                if docs:
                    all_docs.extend(docs)
                    try:
                        os.makedirs(self.config.CACHE_DIR, exist_ok=True)
                        with open(cache_path, "wb") as f:
                            pickle.dump(docs, f)
                    except Exception as e:
                        sys.stderr.write(
                            f"[LOAD]   {os.path.basename(fp)} "
                            f"cache write fail: {e}\n"
                        ); sys.stderr.flush()
                    sys.stderr.write(
                        f"[LOAD]   {os.path.basename(fp)} → {len(docs)} docs\n"
                    ); sys.stderr.flush()
                else:
                    sys.stderr.write(
                        f"[LOAD]   {os.path.basename(fp)} → FAILED\n"
                    ); sys.stderr.flush()
        return all_docs

    def _paragraph_split(self, documents: List[Document]) -> List[Document]:
        heading_pattern = re.compile(r"^#{1,4}\s+\S")
        table_row_pattern = re.compile(r"^\|.+\|")
        paragraph_docs: List[Document] = []
        for doc in documents:
            raw_lines = doc.page_content.split("\n")
            raw_paragraphs = [p.strip() for p in raw_lines if p.strip()]
            merged: List[tuple] = []
            cur_section = ""
            cur_para = ""
            in_table = False
            for para in raw_paragraphs:
                if heading_pattern.match(para):
                    cur_section = para.lstrip("#").strip()
                is_table_row = bool(table_row_pattern.match(para))
                if is_table_row:
                    # 表格行：累积进当前块，不按 MIN_PARAGRAPH_LENGTH 截断
                    new_len = len(cur_para) + len(para) + 1
                    if cur_para and new_len > self.config.MAX_SEMANTIC_CHUNK_SIZE:
                        merged.append((cur_para, cur_section))
                        cur_para = para
                    else:
                        cur_para += "\n" + para if cur_para else para
                    in_table = True
                    continue
                if in_table:
                    # 表格刚结束 → 先flush表格块，再处理当前行
                    in_table = False
                    if cur_para:
                        merged.append((cur_para, cur_section))
                        cur_para = ""
                    # 当前非表格行再进入普通流程
                if len(cur_para) < self.config.MIN_PARAGRAPH_LENGTH:
                    cur_para += "\n" + para if cur_para else para
                else:
                    merged.append((cur_para, cur_section))
                    cur_para = para
            if cur_para:
                merged.append((cur_para, cur_section))
            for para_text, section in merged:
                if len(para_text) >= self.config.MIN_PARAGRAPH_LENGTH:
                    meta = doc.metadata.copy()
                    meta["section_header"] = section
                    paragraph_docs.append(
                        Document(page_content=para_text, metadata=meta)
                    )
        return paragraph_docs

    def _semantic_merge(self, paragraph_docs: List[Document]) -> List[Document]:
        if not paragraph_docs:
            return []
        texts = [d.page_content for d in paragraph_docs]
        metas = [d.metadata for d in paragraph_docs]
        embs = np.array(self.embedding_model(texts))
        final_chunks: List[Document] = []
        cur_texts: List[str] = []
        cur_len = 0
        cur_sections: List[str] = []
        cur_meta = {}
        overlap = self.config.CHUNK_OVERLAP_PARAGRAPHS
        for i in range(len(texts)):
            t, m, tl = texts[i], metas[i], len(texts[i])
            if not cur_texts:
                cur_texts = [t]; cur_len = tl; cur_meta = m
                cur_sections = [m.get("section_header", "")]
                continue
            sim = util.cos_sim(embs[i - 1], embs[i]).item()
            if (sim >= self.config.SEMANTIC_SIMILARITY_THRESHOLD
                    and cur_len + tl <= self.config.MAX_SEMANTIC_CHUNK_SIZE):
                cur_texts.append(t); cur_len += tl
                cur_sections.append(m.get("section_header", ""))
            else:
                best_sec = next((s for s in reversed(cur_sections) if s), "")
                fm = cur_meta.copy(); fm["section_header"] = best_sec
                final_chunks.append(Document(
                    page_content="\n".join(cur_texts), metadata=fm,
                ))
                if overlap > 0 and len(cur_texts) > overlap:
                    ov_texts = cur_texts[-overlap:]
                    ov_secs  = cur_sections[-overlap:]
                else:
                    ov_texts = []; ov_secs = []
                cur_texts = ov_texts + [t]
                cur_len = sum(len(x) for x in cur_texts)
                cur_sections = ov_secs + [m.get("section_header", "")]
                cur_meta = m
        if cur_texts:
            best_sec = next((s for s in reversed(cur_sections) if s), "")
            fm = cur_meta.copy(); fm["section_header"] = best_sec
            final_chunks.append(Document(
                page_content="\n".join(cur_texts), metadata=fm,
            ))
        return final_chunks

    def split_documents(self, documents: List[Document]) -> List[Document]:
        if not documents:
            raise ValueError("未找到可处理的文档，请检查 docs 文件夹")
        para_docs = self._paragraph_split(documents)
        chunks = self._semantic_merge(para_docs)
        valid = [d for d in chunks if len(d.page_content.strip()) >= 20]
        by_file: Dict[str, List[Document]] = {}
        for c in valid:
            fn = c.metadata.get("file_name", "unknown")
            by_file.setdefault(fn, []).append(c)
        for fn, c_list in by_file.items():
            total = len(c_list)
            for i, c in enumerate(c_list):
                c.metadata["chunk_index"] = i + 1
                c.metadata["total_chunks"] = total
                c.metadata["source_file"] = fn
        return valid
