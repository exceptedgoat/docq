"""
RAG 准确度评估模块：检索指标 + 答案质量评分
"""
import json
import os
import sys
import time
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

import numpy as np
from langchain_openai import ChatOpenAI

from .rag import GeneralTerminalRAG
from .config import GeneralConfig


# ═══════════════════════════════════════════
#  数据结构
# ═══════════════════════════════════════════

@dataclass
class EvalResult:
    """单条测试的评估结果"""
    question_id: str
    question: str
    reference_answer: str
    generated_answer: str
    relevant_docs: List[str]
    retrieved_docs: List[str]
    retrieval_recall: float          # 召回率 (relevant ∩ retrieved) / |relevant|
    retrieval_precision: float       # 精确率 (relevant ∩ retrieved) / |retrieved|
    rouge_l_f1: float                # ROUGE-L F1 分数
    llm_judge_score: Optional[float]  # LLM 评判分数 (1-5)
    retrieval_time_ms: float
    generation_time_ms: float
    total_time_ms: float


@dataclass
class ExperimentReport:
    """单次实验的整体报告"""
    config_name: str
    config_desc: str
    results: List[EvalResult] = field(default_factory=list)
    avg_recall: float = 0.0
    avg_precision: float = 0.0
    avg_rouge_l: float = 0.0
    avg_llm_judge: float = 0.0
    avg_retrieval_ms: float = 0.0
    avg_generation_ms: float = 0.0
    success_rate: float = 0.0


# ═══════════════════════════════════════════
#  ROUGE-L 计算
# ═══════════════════════════════════════════

def _lcs_len(a: List[str], b: List[str]) -> int:
    """最长公共子序列长度"""
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[m][n]


def rouge_l_score(reference: str, candidate: str) -> Dict[str, float]:
    """计算 ROUGE-L (F1) 分数"""
    ref_chars = list(reference)
    cand_chars = list(candidate)
    if not ref_chars or not cand_chars:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    lcs = _lcs_len(ref_chars, cand_chars)
    precision = lcs / len(cand_chars) if len(cand_chars) > 0 else 0.0
    recall = lcs / len(ref_chars) if len(ref_chars) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


# ═══════════════════════════════════════════
#  关键词精确匹配评分
# ═══════════════════════════════════════════

def keyword_match_score(reference: str, candidate: str, keywords: List[str]) -> float:
    """检查生成答案是否包含关键词"""
    if not keywords:
        return 1.0
    hits = sum(1 for kw in keywords if kw.lower() in candidate.lower())
    return hits / len(keywords)


# ═══════════════════════════════════════════
#  LLM-as-Judge
# ═══════════════════════════════════════════

LLM_JUDGE_PROMPT = """你是 RAG 答案质量评估专家。根据参考标准答案，评判生成答案的质量。

参考标准答案：{reference}

生成答案：{candidate}

请从以下三个维度打分（1-5 分，5 分为最佳）：

1. 忠实度（Faithfulness）：生成答案是否完全基于参考文档，有没有编造不存在的信息？
2. 准确性（Accuracy）：答案中的数字、时间等关键数据是否与标准答案完全一致？
3. 完整性（Completeness）：是否覆盖了标准答案中的核心信息？

请严格按如下格式输出（仅输出 JSON，不要其他内容）：
{{"faithfulness": 5, "accuracy": 5, "completeness": 5, "overall": 5.0}}
"""


def llm_judge(reference: str, candidate: str, llm: ChatOpenAI) -> float:
    """LLM 评判答案质量，返回 1-5 的综合分"""
    if not candidate or not reference:
        return 1.0
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        prompt = ChatPromptTemplate.from_template(LLM_JUDGE_PROMPT)
        chain = prompt | llm | StrOutputParser()
        result = chain.invoke({"reference": reference, "candidate": candidate})
        # 解析 JSON
        json_match = re.search(r'\{[^}]+\}', result, re.DOTALL)
        if json_match:
            obj = json.loads(json_match.group())
            return float(obj.get("overall", 3.0))
    except Exception as e:
        sys.stderr.write(f"[JUDGE] LLM评判失败: {e}\n")
    return 3.0


# ═══════════════════════════════════════════
#  评估主流程
# ═══════════════════════════════════════════

class RAGEvaluator:
    """RAG 系统评估器"""

    def __init__(self, rag: GeneralTerminalRAG, test_file: str):
        self.rag = rag
        with open(test_file, "r", encoding="utf-8") as f:
            self.test_cases = json.load(f)
        print(f"[EVAL] 加载 {len(self.test_cases)} 条测试用例", flush=True)

    def evaluate_single(self, case: Dict, enable_judge: bool = True) -> EvalResult:
        """评估单条测试"""
        qid = case["id"]
        question = case["question"]
        reference = case["answer"]
        relevant = set(case.get("relevant_docs", []))
        keywords = case.get("keywords", [])

        # ── 检索评估 ──
        t0 = time.time()
        contextualized = self.rag.query_transformer.contextualize_query(
            question, self.rag.conversation_history)
        retrieved_docs = self.rag.retriever.invoke(contextualized)
        t1 = time.time()

        retrieved_files = []
        for doc in retrieved_docs:
            fname = doc.metadata.get("source_file",
                     doc.metadata.get("file_name", "?"))
            retrieved_files.append(fname)
        retrieved_set = set(retrieved_files)

        recall = len(relevant & retrieved_set) / len(relevant) if relevant else 0.0
        precision = len(relevant & retrieved_set) / len(retrieved_set) if retrieved_set else 0.0
        retrieval_ms = (t1 - t0) * 1000

        # ── 生成评估 ──
        t2 = time.time()
        generated = self.rag.generator.generate(contextualized, retrieved_docs)
        t3 = time.time()
        generation_ms = (t3 - t2) * 1000

        rouge = rouge_l_score(reference, generated)
        kw_score = keyword_match_score(reference, generated, keywords)

        judge_score = None
        if enable_judge:
            judge_score = llm_judge(reference, generated, self.rag.llm)

        return EvalResult(
            question_id=qid,
            question=question,
            reference_answer=reference,
            generated_answer=generated,
            relevant_docs=list(relevant),
            retrieved_docs=retrieved_files,
            retrieval_recall=recall,
            retrieval_precision=precision,
            rouge_l_f1=rouge["f1"],
            llm_judge_score=judge_score,
            retrieval_time_ms=retrieval_ms,
            generation_time_ms=generation_ms,
            total_time_ms=retrieval_ms + generation_ms,
        )

    def evaluate_all(self, enable_judge: bool = True, print_progress: bool = True) -> ExperimentReport:
        """评估所有测试用例"""
        results = []
        for i, case in enumerate(self.test_cases):
            if print_progress:
                sys.stderr.write(
                    f"\r[EVAL] [{i+1}/{len(self.test_cases)}] {case['question'][:40]}..."
                ); sys.stderr.flush()
            try:
                r = self.evaluate_single(case, enable_judge=enable_judge)
                results.append(r)
            except Exception as e:
                sys.stderr.write(f"\n[EVAL] {case['id']} 失败: {e}\n")

        if print_progress:
            sys.stderr.write("\n"); sys.stderr.flush()

        success = [r for r in results if r.generated_answer]
        return ExperimentReport(
            config_name="default",
            config_desc="当前配置",
            results=results,
            avg_recall=np.mean([r.retrieval_recall for r in results]) if results else 0.0,
            avg_precision=np.mean([r.retrieval_precision for r in results]) if results else 0.0,
            avg_rouge_l=np.mean([r.rouge_l_f1 for r in results]) if results else 0.0,
            avg_llm_judge=np.mean([r.llm_judge_score for r in results if r.llm_judge_score]) if results else 0.0,
            avg_retrieval_ms=np.mean([r.retrieval_time_ms for r in results]) if results else 0.0,
            avg_generation_ms=np.mean([r.generation_time_ms for r in results]) if results else 0.0,
            success_rate=len(success) / len(results) if results else 0.0,
        )

    def print_report(self, report: ExperimentReport):
        """打印评估报告"""
        print("\n" + "=" * 70)
        print(f"  评估报告：{report.config_name}")
        print(f"  配置说明：{report.config_desc}")
        print("=" * 70)
        print(f"  测试用例数：{len(report.results)}")
        print(f"  成功率：    {report.success_rate * 100:.1f}%")
        print("-" * 70)
        print(f"  {'指标':<20} {'得分':>10}")
        print(f"  {'检索召回率 Recall':<20} {report.avg_recall:.4f}")
        print(f"  {'检索精确率 Precision':<20} {report.avg_precision:.4f}")
        print(f"  {'ROUGE-L F1':<20} {report.avg_rouge_l:.4f}")
        if report.avg_llm_judge > 0:
            print(f"  {'LLM-Judge 综合分':<20} {report.avg_llm_judge:.2f} / 5.0")
        print("-" * 70)
        print(f"  {'平均检索耗时':<20} {report.avg_retrieval_ms:>8.1f} ms")
        print(f"  {'平均生成耗时':<20} {report.avg_generation_ms:>8.1f} ms")
        print("=" * 70)

        # 逐题明细
        print(f"\n{'ID':<5} {'问题':<35} {'Recall':>7} {'ROUGE-L':>8} {'Judge':>6}")
        print("-" * 70)
        for r in report.results:
            judge_str = f"{r.llm_judge_score:.1f}" if r.llm_judge_score else "N/A"
            print(f"{r.question_id:<5} {r.question[:33]:<35} "
                  f"{r.retrieval_recall:>7.3f} {r.rouge_l_f1:>8.4f} {judge_str:>6}")
        print("-" * 70)

    def export_report_json(self, report: ExperimentReport, output_path: str):
        """导出报告为 JSON"""
        data = {
            "config_name": report.config_name,
            "config_desc": report.config_desc,
            "summary": {
                "num_tests": len(report.results),
                "success_rate": report.success_rate,
                "avg_recall": report.avg_recall,
                "avg_precision": report.avg_precision,
                "avg_rouge_l": report.avg_rouge_l,
                "avg_llm_judge": report.avg_llm_judge,
                "avg_retrieval_ms": report.avg_retrieval_ms,
                "avg_generation_ms": report.avg_generation_ms,
            },
            "details": [
                {
                    "id": r.question_id,
                    "question": r.question,
                    "reference": r.reference_answer,
                    "generated": r.generated_answer,
                    "relevant_docs": r.relevant_docs,
                    "retrieved_docs": r.retrieved_docs,
                    "recall": r.retrieval_recall,
                    "precision": r.retrieval_precision,
                    "rouge_l": r.rouge_l_f1,
                    "llm_judge": r.llm_judge_score,
                    "retrieval_ms": r.retrieval_time_ms,
                    "generation_ms": r.generation_time_ms,
                }
                for r in report.results
            ],
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[EVAL] 报告已导出: {output_path}")
