"""
验证异步 stream_chat 功能
测试 MengLong SDK 的异步聊天和流式聊天功能
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from menglong.models.model import Model
from menglong.schemas.chat import User, Assistant, System


async def test_menglong_async():
    """测试 MengLong Provider 异步功能"""
    print("=" * 60)
    print("测试 MengLong Provider 异步功能")
    print("=" * 60)
    
    model = Model(default_model_id="anthropic/global.anthropic.claude-sonnet-4-5-20250929-v1:0")
    
    # 测试异步聊天
    print("\n1. 测试 async_chat:")
    try:
        response = await model.async_chat([
            User("你好，请简单介绍一下你自己。")
        ])
        print(f"Response: {response.text}")
        print(f"Model: {response.model}")
        if response.usage:
            print(f"Usage: {response.usage}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 测试异步流式聊天
    print("\n2. 测试 async_stream_chat:")
    try:
        print("Streaming response: ", end="", flush=True)
        async for chunk in model.async_stream_chat([
            User("用一句话介绍 Python 编程语言。")
        ]):
            if chunk.output and chunk.output.delta and chunk.output.delta.text:
                print(chunk.output.delta.text, end="", flush=True)
        print()  # 换行
    except Exception as e:
        print(f"\nError: {e}")


async def test_openai_async():
    """测试 OpenAI Provider 异步功能"""
    print("\n" + "=" * 60)
    print("测试 OpenAI Provider 异步功能")
    print("=" * 60)
    
    model = Model(default_model_id="openai/gpt-5.1")
    
    # 测试异步聊天
    print("\n1. 测试 async_chat:")
    try:
        response = await model.async_chat([
            User("Hello! Please introduce yourself briefly.")
        ])
        print(f"Response: {response.text}")
        print(f"Model: {response.model}")
        if response.usage:
            print(f"Usage: {response.usage}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 测试异步流式聊天
    print("\n2. 测试 async_stream_chat:")
    try:
        print("Streaming response: ", end="", flush=True)
        async for chunk in model.async_stream_chat([
            User("Describe Python in one sentence.")
        ]):
            if chunk.output and chunk.output.delta and chunk.output.delta.text:
                print(chunk.output.delta.text, end="", flush=True)
        print()  # 换行
    except Exception as e:
        print(f"\nError: {e}")


async def test_concurrent_requests():
    """测试并发异步请求"""
    print("\n" + "=" * 60)
    print("测试并发异步请求")
    print("=" * 60)
    
    model = Model(default_model_id="openai/gpt-5.1")
    
    async def make_request(prompt: str, index: int):
        print(f"\n请求 {index} 开始: {prompt}")
        response = await model.async_chat([User(prompt)])
        print(f"请求 {index} 完成: {response.text[:50]}...")
        return response
    
    # 并发执行多个请求
    prompts = [
        "What is 2+2?",
        "What is the capital of France?",
        "What is Python?"
    ]
    
    try:
        tasks = [make_request(prompt, i+1) for i, prompt in enumerate(prompts)]
        results = await asyncio.gather(*tasks)
        print(f"\n所有 {len(results)} 个请求完成！")
    except Exception as e:
        print(f"Error: {e}")


async def main():
    """主测试函数"""
    print("开始异步功能验证测试\n")
    
    # 测试 MengLong Provider (如果配置了)
    try:
        await test_menglong_async()
    except Exception as e:
        print(f"MengLong Provider 测试跳过: {e}")
    
    # 测试 OpenAI Provider (如果配置了)
    try:
        await test_openai_async()
    except Exception as e:
        print(f"OpenAI Provider 测试跳过: {e}")
    
    # 测试并发请求
    try:
        await test_concurrent_requests()
    except Exception as e:
        print(f"并发请求测试跳过: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
