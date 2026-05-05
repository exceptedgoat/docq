# RAG 智能文档问答系统

基于 DeepSeek + LangChain + ChromaDB 的模块化 RAG 文档问答系统，支持终端交互与 Web SSE 流式对话。

## 项目结构

```
智能计算系统/
├── docs/                        # 待索引文档目录（放 .pdf/.txt/.md/.docx/.xlsx/.pptx）
├── src/
│   ├── __init__.py
│   └── rag/                     # RAG 核心包
│       ├── __init__.py           # 包入口，导出所有公开类
│       ├── config.py             # 全局配置（模型、路径、检索参数）
│       ├── cache.py              # MD5 查询缓存
│       ├── query_transformer.py  # 查询改写 / 多查询生成 / 追问上下文补全
│       ├── processor.py          # 文档加载 → 段落分块 → 语义合并
│       ├── retriever.py          # BM25 + ChromaDB 混合检索 + CrossEncoder 重排序
│       ├── generator.py          # Prompt 模板 + 上下文格式化 + 流式/非流式生成
│       ├── rag.py                # 总控协调器（组装所有模块）
│       ├── web.py                # Flask 路由 + SSE 流式端点
│       ├── templates.py          # 前端 HTML 模板加载器
│       ├── main.py               # 启动入口（终端 / Web 模式切换）
│       ├── extract_templates.py  # 一次性脚本：从 rag_new_v2.py 提取 HTML 模板
│       └── _templates.py         # 提取后的 HTML 模板（由 extract_templates.py 生成）
├── rag_new_v2.py                 # 原单体文件（保留作为参考）
├── requirements.txt              # Python 依赖清单
├── gen_ppt.py                    # PPT 生成脚本
└── README.md                     # 本文件
```

### 模块依赖关系

```
config.py  ← 所有模块
cache.py   ← rag.py
query_transformer.py  ← retriever.py, rag.py
processor.py  ← rag.py
retriever.py  ← rag.py
generator.py  ← rag.py
rag.py        ← web.py, main.py
```

## 快速开始

### 1. 环境准备

```bash
# 激活虚拟环境（Windows PowerShell）
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt --break-system-packages
```

### 2. 配置 API Key

在项目根目录创建 `.env` 文件（国内网络需配置 `HF_ENDPOINT` 镜像）：

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat

# HuggingFace 镜像（国内网络必需，首次启动需下载约 400MB 模型）
HF_ENDPOINT=https://hf-mirror.com
```

### 3. 准备文档

将需要索引的文档放入 `docs/` 文件夹，支持的格式：`.pdf` `.txt` `.md` `.docx` `.doc` `.xlsx` `.xls` `.pptx` `.ppt`

### 4. 提取 Web 前端模板（仅首次，Web 模式需要）

```bash
python src/rag/extract_templates.py
```

### 5. 启动

**终端交互模式：**

```bash
python -m src.rag.main
```

**Web 服务模式（SSE 流式输出 + 多轮对话）：**

```bash
python -m src.rag.main web
```

然后浏览器访问 `http://localhost:7860`

### 6. 生成 PPT

```bash
python gen_ppt.py
```

## 核心特性

| 特性 | 说明 |
|------|------|
| 混合检索 | BM25 关键词匹配 + ChromaDB 语义检索，双路并行 |
| 查询优化 | 查询改写 + Multi-Query 多角度检索 + 追问上下文补全 |
| 智能分块 | 段落分割 + 语义相似度合并，保留章节元数据 |
| CrossEncoder 重排序 | 对候选文档精排，提升 Top-K 质量 |
| SSE 流式输出 | Web 模式支持逐字流式回答 |
| 多轮对话 | 对话历史保留最近 6 轮，支持追问 |
| LLM 缓存 | MD5 查询缓存，相同问题秒出 |

## 配置说明

所有可调参数在 `src/rag/config.py` 的 `GeneralConfig` 类中：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| DOCS_DIR | `./docs` | 文档目录 |
| EMBEDDING_MODEL | `BAAI/bge-small-zh-v1.5` | 嵌入模型 |
| RERANKER_MODEL | `BAAI/bge-reranker-base` | 重排序模型 |
| BM25_K | 12 | BM25 召回数 |
| SEMANTIC_K | 12 | 语义检索召回数 |
| RERANK_TOP_K | 6 | 重排序后保留数 |
| MULTI_QUERY_COUNT | 4 | 多查询生成数 |
| MAX_CONVERSATION_TURNS | 6 | 最大对话轮数 |
| MIN_PARAGRAPH_LENGTH | 50 | 最小段落长度 |
| MAX_SEMANTIC_CHUNK_SIZE | 1200 | 最大语义块大小 |
