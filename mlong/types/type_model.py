# 全局映射
MODEL_LIST = {
    "gpt-4": ("openai", "gpt-4"),
    "claude-3-5-sonnet-20241022": ("anthropic", "claude-3-5-sonnet-20241022"),
    "us.amazon.nova-pro-v1:0": ("aws", "us.amazon.nova-pro-v1:0"),
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0": (
        "aws",
        "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    ),
}

# 示例用法
if __name__ == "__main__":
    # 正确的访问方式
    model = "gpt-4"
    print(f"Model {MODEL_LIST[model][1]} 对应的供应商和模型是: {MODEL_LIST[model][0]}")
