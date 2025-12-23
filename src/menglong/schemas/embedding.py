
"""
嵌入模版(Embedding Template)下的相关的基础数据结构
Embedding Template 是指用于文本嵌入向量计算的数据结构定义。
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# =========================
#         Request
# =========================


class EmbedRequest(BaseModel):
    """嵌入请求"""

    texts: List[str]
    model: str
    input_type: Optional[str] = "search_document"  # 输入类型，如 search_document, search_query 等


# =========================
#         Response
# =========================


class EmbedResponse(BaseModel):
    """嵌入响应模型"""

    embeddings: List[List[float]]  # 嵌入向量列表
    texts: Optional[List[str]] = None  # 原始文本列表
    model: Optional[str] = None  # 使用的模型标识符
    usage: Optional[dict] = None  # token使用统计
