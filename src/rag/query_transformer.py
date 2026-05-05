"""
查询转换：Rewrite · Multi-Query · 追问上下文补全
"""
from typing import List, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from .config import GeneralConfig


class QueryTransformer:
    """查询改写、多查询生成、追问上下文补全"""

    def __init__(self, config: GeneralConfig, llm: ChatOpenAI):
        self.config = config
        self.llm = llm
        self.output_parser = StrOutputParser()

        self.rewrite_prompt = ChatPromptTemplate.from_template("""
你是一个专业的文档检索查询优化助手。
用户的原始问题是：{query}
请将用户的问题改写成更适合文档检索的、书面化、精准完整的问句，仅输出改写后的问句，不要额外解释、不要多余内容。
改写要求：
1.  把口语化表达替换成书面化、专业的表达
2.  补充模糊问题的隐含语义，让问题更完整
3.  仅输出1个改写后的问句，不要序号、不要多余内容
改写后的问句：
""")

        self.multi_query_prompt = ChatPromptTemplate.from_template("""
你是一个专业的文档检索查询优化助手。
用户的原始问题是：{query}
请生成{count}个和原始问题核心含义完全一致，但表达方式、提问角度不同的中文问句，用于并行文档检索。
要求：
1.  每个问句都要完整、独立，适配文档检索场景
2.  覆盖不同的同义词汇、不同的提问角度，最大化覆盖文档中的不同表述
3.  仅输出生成的问句，每行1个，不要序号、不要额外解释、不要多余内容
生成的问句：
""")

        self.contextualize_prompt = ChatPromptTemplate.from_template("""
你是一个对话上下文理解助手。下面是对话历史和新问题，请判断新问题是否是追问。

对话历史：
{history}

新问题：{query}

如果是追问（依赖于对话历史中的某个话题），请将问题改写为一个独立、完整的问题，补充所有隐含的上下文信息。
如果不是追问，直接原样返回新问题。

仅输出改写后的问题（或原问题），不要任何解释：
""")

    # ── Query Rewrite ──
    def rewrite_query(self, original_query: str) -> str:
        if not self.config.ENABLE_QUERY_REWRITE:
            return original_query
        try:
            chain = self.rewrite_prompt | self.llm | self.output_parser
            rewritten = chain.invoke({"query": original_query}).strip()
            return rewritten if rewritten else original_query
        except Exception as e:
            print(f"查询重写失败，使用原始查询：{e}")
            return original_query

    # ── Multi-Query ──
    def generate_multi_queries(self, original_query: str) -> List[str]:
        if not self.config.ENABLE_MULTI_QUERY:
            return [original_query]
        try:
            chain = self.multi_query_prompt | self.llm | self.output_parser
            result = chain.invoke({
                "query": original_query,
                "count": self.config.MULTI_QUERY_COUNT,
            }).strip()
            generated = [q.strip() for q in result.split("\n") if q.strip()]
            return list(set([original_query] + generated))
        except Exception as e:
            print(f"多查询生成失败，使用原始查询：{e}")
            return [original_query]

    # ── 追问上下文补全 ──
    def contextualize_query(self, query: str,
                            history: List[Tuple[str, str]]) -> str:
        if not history:
            return query
        followup_markers = [
            "那", "还有", "它呢", "这个呢",
            "上面", "刚才", "前面", "也", "再",
        ]
        is_short = len(query) <= 12
        has_marker = any(query.strip().startswith(m) for m in followup_markers)
        if not is_short and not has_marker:
            return query
        try:
            history_text = "\n".join(
                [f"用户：{q}\n系统：{a}" for q, a in history[-3:]]
            )
            chain = self.contextualize_prompt | self.llm | self.output_parser
            result = chain.invoke({
                "history": history_text,
                "query": query,
            }).strip()
            return result if result else query
        except Exception as e:
            print(f"追问上下文改写失败：{e}")
            if history:
                return f"{history[-1][0]}。补充问题：{query}"
            return query
