"""
RAG 对比实验框架：多配置 A/B 测试，量化每次优化带来的准确率提升
"""
import json
import os
import sys
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, field

import numpy as np

from .rag import GeneralTerminalRAG
from .config import GeneralConfig
from .evaluate import RAGEvaluator, ExperimentReport


# ═══════════════════════════════════════════
#  实验配置定义
# ═══════════════════════════════════════════

@dataclass
class ExperimentDef:
    """单组实验定义"""
    name: str
    description: str
    config_overrides: Dict  # 覆盖 config 中的字段值


# ═══════════════════════════════════════════
#  预置实验组
# ═══════════════════════════════════════════

def preset_retrieval_strategies() -> List[ExperimentDef]:
    """实验组 A：检索策略对比"""
    return [
        ExperimentDef(
            name="A1-BM25",
            description="仅 BM25 关键词检索",
            config_overrides={
                "RETRIEVAL_MODE": "bm25",
                "ENABLE_RERANK": False,
            },
        ),
        ExperimentDef(
            name="A2-Semantic",
            description="仅 ChromaDB 语义检索",
            config_overrides={
                "RETRIEVAL_MODE": "semantic",
                "ENABLE_RERANK": False,
            },
        ),
        ExperimentDef(
            name="A3-Hybrid",
            description="BM25 + 语义混合检索（无重排序）",
            config_overrides={
                "RETRIEVAL_MODE": "hybrid",
                "ENABLE_RERANK": False,
            },
        ),
        ExperimentDef(
            name="A4-Full",
            description="混合检索 + CrossEncoder 重排序（完整流水线）",
            config_overrides={
                "RETRIEVAL_MODE": "hybrid",
                "ENABLE_RERANK": True,
            },
        ),
    ]


def preset_top_k() -> List[ExperimentDef]:
    """实验组 B：Top-K 值对比"""
    return [
        ExperimentDef(
            name="B1-K3",
            description="混合检索，Top-K=3",
            config_overrides={
                "RETRIEVAL_MODE": "hybrid",
                "ENABLE_RERANK": False,
                "RERANK_TOP_K": 3,
            },
        ),
        ExperimentDef(
            name="B2-K6",
            description="混合检索，Top-K=6（默认）",
            config_overrides={
                "RETRIEVAL_MODE": "hybrid",
                "ENABLE_RERANK": False,
                "RERANK_TOP_K": 6,
            },
        ),
        ExperimentDef(
            name="B3-K12",
            description="混合检索，Top-K=12",
            config_overrides={
                "RETRIEVAL_MODE": "hybrid",
                "ENABLE_RERANK": False,
                "RERANK_TOP_K": 12,
            },
        ),
    ]


def preset_query_optimizations() -> List[ExperimentDef]:
    """实验组 C：查询优化策略对比"""
    return [
        ExperimentDef(
            name="C1-Raw",
            description="原始查询，无改写无多查询",
            config_overrides={
                "ENABLE_QUERY_REWRITE": False,
                "ENABLE_MULTI_QUERY": False,
            },
        ),
        ExperimentDef(
            name="C2-Rewrite",
            description="仅查询改写",
            config_overrides={
                "ENABLE_QUERY_REWRITE": True,
                "ENABLE_MULTI_QUERY": False,
            },
        ),
        ExperimentDef(
            name="C3-MultiQuery",
            description="仅多查询生成",
            config_overrides={
                "ENABLE_QUERY_REWRITE": False,
                "ENABLE_MULTI_QUERY": True,
            },
        ),
        ExperimentDef(
            name="C4-Full",
            description="查询改写 + 多查询（完整）",
            config_overrides={
                "ENABLE_QUERY_REWRITE": True,
                "ENABLE_MULTI_QUERY": True,
            },
        ),
    ]


def preset_all() -> List[ExperimentDef]:
    """所有预置实验"""
    exps = []
    exps.extend(preset_retrieval_strategies())
    exps.extend(preset_top_k())
    exps.extend(preset_query_optimizations())
    return exps


PRESET_GROUPS = {
    "retrieval": ("检索策略对比", preset_retrieval_strategies),
    "topk": ("Top-K 值对比", preset_top_k),
    "query": ("查询优化策略对比", preset_query_optimizations),
    "all": ("全部实验", preset_all),
}


# ═══════════════════════════════════════════
#  对比报告数据结构
# ═══════════════════════════════════════════

@dataclass
class ComparisonReport:
    """多组实验对比报告"""
    experiments: List[ExperimentReport] = field(default_factory=list)
    best_recall: str = ""
    best_precision: str = ""
    best_rouge_l: str = ""
    best_llm_judge: str = ""
    best_overall: str = ""


# ═══════════════════════════════════════════
#  实验运行器
# ═══════════════════════════════════════════

class RAGExperimentRunner:
    """RAG 对比实验运行器：同一测试集跑多组配置，输出对比报告"""

    def __init__(self, test_file: str, rag: GeneralTerminalRAG):
        self.test_file = test_file
        self.rag = rag
        self._save_defaults()

    def _save_defaults(self):
        """保存当前配置的默认值，用于实验后恢复"""
        cfg = self.rag.config
        self._defaults = {
            "RETRIEVAL_MODE": cfg.RETRIEVAL_MODE,
            "ENABLE_RERANK": cfg.ENABLE_RERANK,
            "ENABLE_QUERY_REWRITE": cfg.ENABLE_QUERY_REWRITE,
            "ENABLE_MULTI_QUERY": cfg.ENABLE_MULTI_QUERY,
            "RERANK_TOP_K": cfg.RERANK_TOP_K,
        }

    def _apply_overrides(self, overrides: Dict):
        """将配置覆盖应用到当前 config"""
        cfg = self.rag.config
        for key, value in overrides.items():
            if hasattr(cfg, key):
                setattr(cfg, key, value)
            else:
                sys.stderr.write(f"[EXP] 警告：未知配置项 {key}\n")

    def _restore_defaults(self):
        """恢复默认配置"""
        self._apply_overrides(self._defaults)

    def run_single(self, exp_def: ExperimentDef, enable_judge: bool = True) -> ExperimentReport:
        """运行单个实验配置"""
        sys.stderr.write(f"\n{'=' * 60}\n")
        sys.stderr.write(f"[EXP] 实验: {exp_def.name} — {exp_def.description}\n")
        sys.stderr.write(f"[EXP] 配置覆盖: {exp_def.config_overrides}\n")
        sys.stderr.write(f"{'=' * 60}\n\n")
        sys.stderr.flush()

        self._apply_overrides(exp_def.config_overrides)

        evaluator = RAGEvaluator(self.rag, self.test_file)
        report = evaluator.evaluate_all(enable_judge=enable_judge, print_progress=True)
        report.config_name = exp_def.name
        report.config_desc = exp_def.description

        self._restore_defaults()
        return report

    def run_group(self, group_key: str, enable_judge: bool = True) -> ComparisonReport:
        """运行一组预置实验"""
        if group_key not in PRESET_GROUPS:
            raise ValueError(f"未知实验组: {group_key}，可选: {list(PRESET_GROUPS.keys())}")

        group_label, factory = PRESET_GROUPS[group_key]
        exps = factory()

        print(f"\n{'#' * 70}")
        print(f"#  实验组: {group_label} ({len(exps)} 组配置)")
        print(f"{'#' * 70}\n")

        reports = []
        for i, exp_def in enumerate(exps):
            print(f"\n--- [{i+1}/{len(exps)}] {exp_def.name} ---")
            t_start = time.time()
            report = self.run_single(exp_def, enable_judge=enable_judge)
            elapsed = time.time() - t_start
            print(f"[EXP] {exp_def.name} 完成，耗时 {elapsed:.1f}s")
            reports.append(report)

        comparison = self._build_comparison(reports)
        return comparison

    def _build_comparison(self, reports: List[ExperimentReport]) -> ComparisonReport:
        """构建对比报告"""
        if not reports:
            return ComparisonReport()

        # 找出各项最佳
        best_recall = max(reports, key=lambda r: r.avg_recall)
        best_precision = max(reports, key=lambda r: r.avg_precision)
        best_rouge = max(reports, key=lambda r: r.avg_rouge_l)

        judge_reports = [r for r in reports if r.avg_llm_judge > 0]
        best_judge = max(judge_reports, key=lambda r: r.avg_llm_judge) if judge_reports else reports[0]

        return ComparisonReport(
            experiments=reports,
            best_recall=best_recall.config_name,
            best_precision=best_precision.config_name,
            best_rouge_l=best_rouge.config_name,
            best_llm_judge=best_judge.config_name,
            best_overall=best_judge.config_name,
        )

    def print_comparison(self, comparison: ComparisonReport):
        """打印对比报告"""
        reports = comparison.experiments
        if not reports:
            print("无实验结果")
            return

        print("\n" + "=" * 90)
        print("                         RAG 配置对比实验结果")
        print("=" * 90)

        # 汇总表头
        header = (f"{'实验':<18} {'Recall':>8} {'Precision':>10} {'ROUGE-L':>8} "
                  f"{'Judge':>7} {'检索ms':>8} {'生成ms':>8} {'成功率':>8}")
        print(header)
        print("-" * 90)

        for r in reports:
            judge_str = f"{r.avg_llm_judge:.2f}" if r.avg_llm_judge > 0 else "N/A"
            print(f"{r.config_name:<18} {r.avg_recall:>8.4f} {r.avg_precision:>10.4f} "
                  f"{r.avg_rouge_l:>8.4f} {judge_str:>7} "
                  f"{r.avg_retrieval_ms:>8.1f} {r.avg_generation_ms:>8.1f} "
                  f"{r.success_rate*100:>7.1f}%")

        print("-" * 90)
        print(f"  最佳召回率:     {comparison.best_recall}")
        print(f"  最佳精确率:     {comparison.best_precision}")
        print(f"  最佳 ROUGE-L:   {comparison.best_rouge_l}")
        if comparison.best_llm_judge:
            print(f"  最佳 LLM-Judge: {comparison.best_llm_judge}")
        print("=" * 90)

        # 详细对比：按实验逐题
        print(f"\n{'─' * 90}")
        print("  逐题对比明细")
        print(f"{'─' * 90}")

        # 表头：ID + 问题 + 各组 recall/rouge
        col_widths = [4, 24] + [10] * len(reports)
        header2 = f"{'ID':<4} {'问题':<24}"
        for r in reports:
            header2 += f" {r.config_name:>10}"
        print(header2)
        print("-" * (4 + 24 + 10 * len(reports)))

        for i in range(len(reports[0].results)):
            qid = reports[0].results[i].question_id
            qtext = reports[0].results[i].question[:22]
            line = f"{qid:<4} {qtext:<24}"
            for r in reports:
                if i < len(r.results):
                    line += f" {r.results[i].rouge_l_f1:>10.4f}"
                else:
                    line += f" {'N/A':>10}"
            print(line)

        print(f"{'─' * 90}\n")

    def export_comparison(self, comparison: ComparisonReport, output_dir: str = "./eval_results"):
        """导出对比报告为 JSON"""
        os.makedirs(output_dir, exist_ok=True)

        data = {
            "num_experiments": len(comparison.experiments),
            "best": {
                "recall": comparison.best_recall,
                "precision": comparison.best_precision,
                "rouge_l": comparison.best_rouge_l,
                "llm_judge": comparison.best_llm_judge,
            },
            "experiments": [],
        }

        for r in comparison.experiments:
            exp_data = {
                "name": r.config_name,
                "description": r.config_desc,
                "summary": {
                    "num_tests": len(r.results),
                    "success_rate": r.success_rate,
                    "avg_recall": r.avg_recall,
                    "avg_precision": r.avg_precision,
                    "avg_rouge_l": r.avg_rouge_l,
                    "avg_llm_judge": r.avg_llm_judge,
                    "avg_retrieval_ms": r.avg_retrieval_ms,
                    "avg_generation_ms": r.avg_generation_ms,
                },
                "details": [
                    {
                        "id": rr.question_id,
                        "question": rr.question,
                        "reference": rr.reference_answer,
                        "generated": rr.generated_answer,
                        "relevant_docs": rr.relevant_docs,
                        "retrieved_docs": rr.retrieved_docs,
                        "recall": rr.retrieval_recall,
                        "precision": rr.retrieval_precision,
                        "rouge_l": rr.rouge_l_f1,
                        "llm_judge": rr.llm_judge_score,
                        "retrieval_ms": rr.retrieval_time_ms,
                        "generation_ms": rr.generation_time_ms,
                    }
                    for rr in r.results
                ],
            }
            data["experiments"].append(exp_data)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        path = os.path.join(output_dir, f"comparison_{timestamp}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[EXP] 对比报告已导出: {path}")
        return path


# ═══════════════════════════════════════════
#  CLI 入口
# ═══════════════════════════════════════════

def main():
    """命令行入口：python -m src.rag.experiment [group]"""
    import argparse

    parser = argparse.ArgumentParser(
        description="RAG 对比实验：多配置 A/B 测试")
    parser.add_argument(
        "group", nargs="?", default="all",
        choices=list(PRESET_GROUPS.keys()),
        help=f"实验组名称: {list(PRESET_GROUPS.keys())}")
    parser.add_argument(
        "--test-file", default="./tests/test_questions.json",
        help="测试用例 JSON 文件路径")
    parser.add_argument(
        "--no-judge", action="store_true",
        help="禁用 LLM-Judge 评分（加速实验）")
    parser.add_argument(
        "--output-dir", default="./eval_results",
        help="结果导出目录")
    parser.add_argument(
        "--docs-dir", default=None,
        help="文档目录（覆盖 config 中的设置）")
    args = parser.parse_args()

    # 初始化 RAG
    config = GeneralConfig()
    if args.docs_dir:
        config.DOCS_DIR = args.docs_dir
    config.ENABLE_LLM_CACHE = False  # 实验时不使用缓存
    config.DEBUG_MODE = False

    print("正在初始化 RAG 系统...")
    rag = GeneralTerminalRAG(config)

    # 运行实验
    runner = RAGExperimentRunner(args.test_file, rag)
    comparison = runner.run_group(args.group, enable_judge=not args.no_judge)

    # 输出结果
    runner.print_comparison(comparison)
    runner.export_comparison(comparison, args.output_dir)

    print("\n实验完成。")


if __name__ == "__main__":
    main()
