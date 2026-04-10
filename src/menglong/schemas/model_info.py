"""
ModelInfo schema — 描述一个可用模型的基础信息
"""

from typing import Optional
from pydantic import BaseModel


class ModelInfo(BaseModel):
    """可用模型的简要描述"""

    id: str  # 模型的完整 ID，可直接传给 Model(model_id=...)
    provider: str  # provider 名称，如 openai / deepseek / aws / anthropic / google
    display_name: Optional[str] = None  # 可读名称（部分 provider 提供）
    created_at: Optional[int] = None  # Unix 时间戳（部分 provider 提供）

    def __str__(self) -> str:
        return f"{self.provider}/{self.id}"
