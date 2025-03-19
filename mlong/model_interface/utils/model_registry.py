from typing import Dict, Tuple

MODEL_REGISTRY: Dict[str, Tuple[str, str]] = {
    "gpt-4o": ("openai", "gpt-4o"),
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
    "cohere.embed-multilingual-v3": (
        "aws",
        "cohere.embed-multilingual-v3",
    ),
    "us.deepseek.r1-v1:0":(
        "aws",
        "us.deepseek.r1-v1:0",
    ),
    "deepseek-chat":(
        "deepseek",
        "deepseek-chat",
    ),
    "deepseek-reasoner":(
        "deepseek",
        "deepseek-reasoner",
    ),
    "Claude-3.7-Sonnet":(
        "poe",
        "Claude-3.7-Sonnet",
    ),
        
}