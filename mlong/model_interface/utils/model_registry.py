from typing import Dict, Tuple

MODEL_REGISTRY: Dict[str, Tuple[str, str]] = {
    "gpt-4": ("openai", "gpt-4o"),
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
}