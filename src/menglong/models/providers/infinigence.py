from typing import List, Generator, Dict, Any, Optional
import os
from menglong.models.providers.openai import OpenAIProvider
from menglong.models.providers.registry import ProviderRegistry
from menglong.utils.config.config_type import ProviderConfig

@ProviderRegistry.register("infinigence")
class InfinigenceProvider(OpenAIProvider):
    """
    Infinigence (无问芯穹) Provider
    由于其高度兼容 OpenAI 协议，直接继承自 OpenAIProvider。
    """
    
    def __init__(self, config: ProviderConfig):
        # 如果配置中没提供 base_url，则使用 Infinigence 默认值
        if not config.base_url:
            config.base_url = "https://cloud.infini-ai.com/maas/v1"
            
        # 允许从环境变量读取 key
        if not config.api_key:
            config.api_key = os.getenv("INFINIGENCE_API_KEY")
            
        super().__init__(config)

    # 如果未来 Infinigence 有特殊的推理字段映射，可以在此处覆盖 _normalize_response
