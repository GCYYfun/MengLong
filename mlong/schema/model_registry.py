from typing import Dict, Tuple, Optional

# 模型注册表：映射模型ID到(提供商, 模型名称)元组
MODEL_REGISTRY: Dict[str, Tuple[str, str]] = {
    "gpt-4": ("openai", "gpt-4"),
    "claude-3-5-sonnet-20241022": ("anthropic", "claude-3-5-sonnet-20241022"),
    "us.amazon.nova-pro-v1:0": ("aws", "us.amazon.nova-pro-v1:0"),
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0": (
        "aws",
        "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    ),
    "us.anthropic.claude-3-7-sonnet-20250219-v1:0": (
        "aws",
        "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    ),
}


def register_model(model_id: str, provider: str, model_name: str) -> None:
    """注册新模型到全局注册表
    
    Args:
        model_id: 模型唯一标识符
        provider: 模型提供商
        model_name: 提供商内部的模型名称
    """
    MODEL_REGISTRY[model_id] = (provider, model_name)


def get_model_info(model_id: str) -> Optional[Tuple[str, str]]:
    """获取模型信息
    
    Args:
        model_id: 模型唯一标识符
        
    Returns:
        包含(提供商, 模型名称)的元组，如果模型不存在则返回None
    """
    return MODEL_REGISTRY.get(model_id)


def list_models() -> Dict[str, Tuple[str, str]]:
    """获取所有已注册模型的列表
    
    Returns:
        模型注册表的副本
    """
    return MODEL_REGISTRY.copy()


def list_models_by_provider(provider: str) -> Dict[str, Tuple[str, str]]:
    """获取指定提供商的所有模型
    
    Args:
        provider: 提供商名称
        
    Returns:
        该提供商的所有模型映射
    """
    return {k: v for k, v in MODEL_REGISTRY.items() if v[0] == provider}