# RAG 智能文档问答系统

基于 DeepSeek + LangChain + ChromaDB 的模块化 RAG 文档问答系统，支持终端交互与 Web SSE 流式对话。

## 项目结构

```
智能计算系统/
├── docs/                        # 待索引文档目录（放 .pdf/.txt/.md/.docx/.xlsx/.pptx）
├── tests/
│   └── test_questions.json      # RAG 准确度测试用例（15 题，含标准答案）
├── eval_results/                # 评估报告导出目录
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
│       ├── evaluate.py           # RAG 准确度评估（Recall/Precision/ROUGE-L/LLM-Judge）
│       ├── experiment.py         # 对比实验框架（多配置 A/B 测试）
│       ├── conversation_store.py # 多对话持久化存储
│       ├── web.py                # Flask 路由 + SSE 流式端点
│       ├── templates.py          # 前端 HTML 模板加载器
│       ├── main.py               # 启动入口（终端 / Web 模式切换）
│       ├── extract_templates.py  # 一次性脚本：从 rag_new_v2.py 提取 HTML 模板
│       └── _templates.py         # 提取后的 HTML 模板（由 extract_templates.py 生成）
├── requirements.txt              # Python 依赖清单
└── README.md                     # 本文件
```

### 模块依赖关系

```
config.py  ← 所有模块
cache.py   ← rag.py
query_transformer.py  ← retriever.py, rag.py
processor.py  ← rag.py
retriever.py  ← rag.py, evaluate.py, experiment.py
generator.py  ← rag.py, evaluate.py
rag.py        ← web.py, main.py, evaluate.py, experiment.py
evaluate.py   ← experiment.py
```

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt --break-system-packages
```

### 2. 配置 API Key

在项目根目录创建 `.env` 文件：

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
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


| 特性               | 说明                                 |
| ---------------- | ---------------------------------- |
| 混合检索             | BM25 关键词匹配 + ChromaDB 语义检索，双路并行    |
| 查询优化             | 查询改写 + Multi-Query 多角度检索 + 追问上下文补全 |
| 智能分块             | 段落分割 + 语义相似度合并，保留章节元数据             |
| CrossEncoder 重排序 | 对候选文档精排，提升 Top-K 质量                |
| SSE 流式输出         | Web 模式支持逐字流式回答                     |
| 多轮对话             | 对话历史保留最近 6 轮，支持追问                  |
| LLM 缓存           | MD5 查询缓存，相同问题秒出                    |
| 准确度评估           | Recall/Precision/ROUGE-L/LLM-Judge 四维评分 |
| 对比实验             | 多配置 A/B 测试，量化每次优化的准确率提升        |


## 配置说明

所有可调参数在 `src/rag/config.py` 的 `GeneralConfig` 类中：


| 参数                      | 默认值                      | 说明       |
| ----------------------- | ------------------------ | -------- |
| DOCS_DIR                | `./docs`                 | 文档目录     |
| EMBEDDING_MODEL         | `BAAI/bge-small-zh-v1.5` | 嵌入模型     |
| RERANKER_MODEL          | `BAAI/bge-reranker-base` | 重排序模型    |
| BM25_K                  | 12                       | BM25 召回数 |
| SEMANTIC_K              | 12                       | 语义检索召回数  |
| RERANK_TOP_K            | 6                        | 重排序后保留数  |
| MULTI_QUERY_COUNT       | 4                        | 多查询生成数   |
| MAX_CONVERSATION_TURNS  | 6                        | 最大对话轮数   |


## 准确度评估

系统内置了完整的 RAG 评估模块，支持检索指标和答案质量的双维度评分。

### 评估指标

- **检索召回率 (Recall@K)**：相关文档中有多少被检索到
- **检索精确率 (Precision@K)**：检索到的文档中有多少是相关的
- **ROUGE-L F1**：生成答案与标准答案的最长公共子序列相似度
- **LLM-Judge 综合分 (1-5)**：从忠实度、准确性、完整性三个维度由 LLM 评判
- **关键词命中率**：生成答案对标准答案关键词的覆盖比例

### 运行评估

```bash
# 在 Python 中交互式评估
python -c "
from src.rag import GeneralTerminalRAG
from src.rag.evaluate import RAGEvaluator

rag = GeneralTerminalRAG()
evaluator = RAGEvaluator(rag, './tests/test_questions.json')
report = evaluator.evaluate_all(enable_judge=True)
evaluator.print_report(report)
evaluator.export_report_json(report, './eval_results/report.json')
"
```

### 测试用例格式

`tests/test_questions.json` 中每条用例包含：

```json
{
  "id": "q01",
  "question": "BETA API每分钟限流是多少？",
  "answer": "每密钥每分钟请求上限为 60 次。",
  "relevant_docs": ["doc_beta.md", "doc_products.md"],
  "keywords": ["Beta", "60", "每分钟", "限流", "请求上限"]
}
```


## 对比实验

实验框架支持多组配置的 A/B 测试，量化每次 RAG 优化带来的准确率提升。

### 预置实验组

| 实验组 | 命令参数 | 内容 |
| ------ | -------- | ---- |
| 检索策略对比 | `retrieval` | BM25-only / Semantic-only / Hybrid / Full-pipeline(含Reranker) |
| Top-K 值对比 | `topk` | K=3 / K=6(默认) / K=12 |
| 查询优化策略对比 | `query` | 无优化 / 仅改写 / 仅多查询 / 完整优化 |
| 全部实验 | `all` | 上述三组合并运行 |

### 运行实验

```bash
# 运行全部实验（11 组配置）
python -m src.rag.experiment

# 运行单组实验
python -m src.rag.experiment retrieval
python -m src.rag.experiment topk
python -m src.rag.experiment query

# 禁用 LLM-Judge 加速实验
python -m src.rag.experiment retrieval --no-judge

# 指定文档目录
python -m src.rag.experiment all --docs-dir ./my_docs

# 自定义输出目录
python -m src.rag.experiment topk --output-dir ./my_results
```

实验结果会以表格形式打印到终端，同时导出为 `eval_results/comparison_YYYYMMDD_HHMMSS.json`。

### 检索模式说明

通过 `config.py` 中的配置项控制：

- `RETRIEVAL_MODE`：`"bm25"` / `"semantic"` / `"hybrid"`（混合）
- `ENABLE_RERANK`：`True` 启用 CrossEncoder 重排序
- `ENABLE_QUERY_REWRITE`：控制是否进行查询改写
- `ENABLE_MULTI_QUERY`：控制是否生成多角度查询变体
- `RERANK_TOP_K`：最终保留的文档数量
| MIN_PARAGRAPH_LENGTH    | 50                       | 最小段落长度   |
| MAX_SEMANTIC_CHUNK_SIZE | 1200                     | 最大语义块大小  |


