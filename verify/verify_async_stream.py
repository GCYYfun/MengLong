"""
简单的异步流式聊天测试
快速验证 async_stream_chat 功能
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from menglong.models.model import Model


async def simple_async_stream_test():
    """简单的异步流式测试"""
    # 使用 OpenAI provider (假设已配置)

    test_models = [
        "openai/gpt-5.1",
        "deepseek/deepseek-chat",
        "aws/global.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "anthropic/global.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "google/gemini-3-pro-preview",
        "infinigence/claude-sonnet-4-20250514",
    ]
    model = Model()
    for model_id in test_models:
        print(f"\n\n测试模型: {model_id}")
        model.default_model_id = model_id

        print("异步流式聊天测试:")
        print("-" * 40)
        print("问题: 用一句话介绍 Python\n")
        print("回答: ", end="", flush=True)

        async for chunk in model.async_stream_chat(
            [{"role": "user", "content": "用一句话介绍 Python 编程语言"}]
        ):
            if chunk.output and chunk.output.delta and chunk.output.delta.text:
                print(chunk.output.delta.text, end="", flush=True)

        print("\n" + "-" * 40)
        print("测试完成！")


if __name__ == "__main__":
    asyncio.run(simple_async_stream_test())
