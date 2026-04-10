from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, ConfigDict


class ModelConfig(BaseModel):
    """单个模型的配置"""

    temperature: float = 0.7
    max_tokens: int = 4096
    dimensions: Optional[int] = None  # 用于 embedding 模型

    model_config = ConfigDict(extra="allow")


class ProviderConfig(BaseModel):
    """通用 Provider 配置 (取代原来的 BaseProviderConfig 及各个子类)"""

    api_key: str = ""
    base_url: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3

    # 额外参数 (AWS region, Google project 等)
    extra_fields: Dict[str, Any] = Field(default_factory=dict)

    models: Dict[str, ModelConfig] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class SystemConfig(BaseModel):
    """系统配置"""

    debug: bool = False
    log_level: str = "INFO"


class DefaultConfig(BaseModel):
    """默认配置"""

    model_id: str = ""
    embedding_model_id: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 30


class Config(BaseModel):
    """MengLong 主配置"""

    default: DefaultConfig = Field(default_factory=DefaultConfig)
    system: SystemConfig = Field(default_factory=SystemConfig)
    providers: Dict[str, ProviderConfig] = Field(default_factory=dict)
