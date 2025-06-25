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
    "us.deepseek.r1-v1:0": (
        "aws",
        "us.deepseek.r1-v1:0",
    ),
    "deepseek-chat": (
        "deepseek",
        "deepseek-chat",
    ),
    "deepseek-reasoner": (
        "deepseek",
        "deepseek-reasoner",
    ),
    "Claude-3.7-Sonnet": (
        "poe",
        "Claude-3.7-Sonnet",
    ),
    "us.meta.llama4-scout-17b-instruct-v1:0": (
        "aws",
        "us.meta.llama4-scout-17b-instruct-v1:0",
    ),
    "us.anthropic.claude-sonnet-4-20250514-v1:0": (
        "aws",
        "us.anthropic.claude-sonnet-4-20250514-v1:0",
    ),
    "us.anthropic.claude-opus-4-20250514-v1:0": (
        "aws",
        "us.anthropic.claude-opus-4-20250514-v1:0",
    ),
    "deepseek-r1": (
        "infinigence",
        "deepseek-r1",
    ),
    "claude-3-7-sonnet-20250219": (
        "infinigence",
        "claude-3-7-sonnet-20250219",
    ),
    "claude-4-sonnet-20250514": (
        "infinigence",
        "claude-4-sonnet-20250514",
    ),
}

MODEL_PRICES: Dict[str, float] = {
    "gpt-4o": {
        "input": 0.0003,
        "cache_input": 0.0003,
        "output": 0.0006,
    },
    "claude-3-5-sonnet-20241022": {
        "input": 0.00025,
        "cache_input": 0.00025,
        "output": 0.0005,
    },
}
