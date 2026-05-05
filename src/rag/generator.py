"""
生成模块：Prompt 模板 · 上下文格式化 · 流式/非流式生成
"""
from typing import List, Tuple, Generator

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI


class GeneralGenerator:
    """基于 DeepSeek 的生成器，支持单轮与多轮对话"""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

        self.prompt = ChatPromptTemplate.from_template("""
你是文档问答助手，严格基于参考文档回答。

每个参考片段以 [文件名 · 片段 N/M · 所属章节] 开头，帮助你了解信息来源。

规则：
1. 只基于参考文档回答，不编造任何不存在的信息。
2. 数字、时间、百分比等数据必须与参考文档完全一致，一字不改。
3. 参考文档中确实没有相关信息时，回答"参考文档中未找到相关内容"。
4. 用中文简洁回答，不需要标注来源。

参考文档：
{context}

用户问题：{question}

回答：
""")

        self.prompt_with_history = ChatPromptTemplate.from_template("""
你是文档问答助手，严格基于参考文档回答。

每个参考片段以 [文件名 · 片段 N/M · 所属章节] 开头，帮助你了解信息来源。

对话历史：
{history}

规则：
1. 只基于参考文档回答，不编造任何不存在的信息。
2. 数字、时间、百分比等数据必须与参考文档完全一致，一字不改。
3. 如果用户的问题是对话的延续（如"那X呢"、"还有呢"），结合对话历史理解完整意图。
4. 参考文档中确实没有相关信息时，回答"参考文档中未找到相关内容"。
5. 用中文简洁回答，不需要标注来源。

参考文档：
{context}

用户问题：{question}

回答：
""")

    def format_docs(self, docs: List[Document]) -> str:
        """将检索文档格式化为带元数据头的上下文文本"""
        parts = []
        for doc in docs:
            fname = doc.metadata.get(
                "source_file", doc.metadata.get("file_name", "?"))
            idx = doc.metadata.get("chunk_index", "?")
            total = doc.metadata.get("total_chunks", "?")
            section = doc.metadata.get("section_header", "")
            header = f"[{fname} · 片段 {idx}/{total}"
            if section:
                header += f" · {section}"
            header += "]"
            parts.append(f"{header}\n{doc.page_content}")
        return "\n\n".join(parts)

    def generate(self, query: str,
                 retrieved_docs: List[Document]) -> str:
        context = self.format_docs(retrieved_docs)
        chain = (
            {"context": lambda _: context, "question": RunnablePassthrough()}
            | self.prompt | self.llm | StrOutputParser()
        )
        return chain.invoke(query)

    def generate_stream(
        self, query: str, retrieved_docs: List[Document],
        conversation_history: List[Tuple[str, str]] | None = None,
    ) -> Generator[str, None, None]:
        context = self.format_docs(retrieved_docs)
        if conversation_history and len(conversation_history) > 0:
            history_text = "\n".join(
                [f"用户：{q}\n系统：{a}" for q, a in conversation_history])
            prompt_text = self.prompt_with_history.format(
                history=history_text, context=context, question=query)
        else:
            prompt_text = self.prompt.format(context=context, question=query)
        messages = [HumanMessage(content=prompt_text)]
        for chunk in self.llm.stream(messages):
            if chunk.content:
                yield chunk.content
