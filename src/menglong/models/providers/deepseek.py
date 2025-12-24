import os
import json
from typing import List, Generator, Dict, Any

from menglong.models.providers.openai import OpenAIProvider
from menglong.models.providers.registry import ProviderRegistry
from menglong.schemas.chat import (
    Message, Response, StreamResponse, 
    Output, Content, Usage, Action,
    StreamOutput, Delta
)
from menglong.utils.config.config_type import ProviderConfig

@ProviderRegistry.register("deepseek")
class DeepSeekProvider(OpenAIProvider):
    """
    DeepSeek Provider
    继承自 OpenAIProvider，因为其 API 高度兼容 OpenAI。
    扩展了对 reasoning_content (思维链) 的支持。
    """
    
    def __init__(self, config: ProviderConfig):
        # 如果配置中没提供 base_url，则使用 DeepSeek 默认值
        if not config.base_url:
            config.base_url = "https://api.deepseek.com"
            
        # 允许从环境变量读取 key
        if not config.api_key:
            config.api_key = os.getenv("DEEPSEEK_API_KEY")
            
        super().__init__(config)

    def _normalize_response(self, response: Any, model: str) -> Response:
        """支持 reasoning_content 的归一化"""
        res = super()._normalize_response(response, model)
        
        # 提取推理内容 (DeepSeek 特有字段)
        choice = response.choices[0]
        deepseek_reasoning = getattr(choice.message, "reasoning_content", None)
        
        if deepseek_reasoning:
            res.output.content.reasoning = deepseek_reasoning
            
        return res

    def _normalize_stream_chunk(self, chunk: Any, model: str) -> StreamResponse:
        """支持 reasoning_content 的流式归一化"""
        res = super()._normalize_stream_chunk(chunk, model)
        
        if not chunk.choices:
            return res
            
        delta = chunk.choices[0].delta
        deepseek_reasoning = getattr(delta, "reasoning_content", None)
        
        if deepseek_reasoning:
            if res.output.delta:
                res.output.delta.reasoning = deepseek_reasoning
                
        return res
