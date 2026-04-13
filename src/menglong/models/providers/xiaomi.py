from typing import List, Generator, Dict, Any, Optional
import os
from menglong.models.providers.openai import OpenAIProvider
from menglong.models.providers.registry import ProviderRegistry
from menglong.utils.config.config_type import ProviderConfig


@ProviderRegistry.register("xiaomi")
class XiaomiProvider(OpenAIProvider):
    """
    Xiaomi Provider
    由于其高度兼容 OpenAI 协议，直接继承自 OpenAIProvider。
    """

    def __init__(self, config: ProviderConfig):
        # 如果配置中没提供 base_url，可以设置一个默认值
        # 如果没有明确的公开默认 URL，建议用户在配置中指定
        if not config.base_url:
            config.base_url = os.getenv(
                "XIAOMI_BASE_URL", "https://api.xiaomimimo.com/v1"
            )

        # 允许从环境变量读取 key
        if not config.api_key:
            config.api_key = os.getenv("XIAOMI_API_KEY")

        super().__init__(config)

    # 如果未来 Miaomi 有特殊的推理字段映射或其他特殊处理，可以在此处覆盖相关方法
