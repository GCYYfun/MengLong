#!/usr/bin/env python3
"""
测试 DuckDuckGo 搜索功能
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from menglong.agents.chat.chat_agent import ChatAgent, ChatMode, tool
from menglong.utils.log import rich_print, RichMessageType
import time
from typing import Dict, Any


@tool(name="web_search", description="使用DuckDuckGo进行网络搜索")
def web_search(query: str, max_results: int = 3) -> Dict[str, Any]:
    """使用DuckDuckGo进行真实的网络搜索"""
    try:
        from duckduckgo_search import DDGS

        rich_print(f"🔍 正在搜索: {query}", RichMessageType.INFO)

        results = []
        with DDGS() as ddgs:
            # 执行搜索，限制结果数量
            search_results = list(ddgs.text(query, max_results=max_results))

            for i, result in enumerate(search_results):
                results.append(
                    {
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                        "snippet": result.get("body", ""),
                        "relevance": 1.0 - (i * 0.1),  # 按顺序递减相关性
                    }
                )

        rich_print(f"✅ 搜索完成，找到 {len(results)} 个结果", RichMessageType.SUCCESS)

        return {
            "query": query,
            "results": results,
            "total_found": len(results),
            "search_time": time.time(),
            "source": "DuckDuckGo",
        }

    except Exception as e:
        rich_print(f"❌ 搜索出错: {str(e)}", RichMessageType.ERROR)
        return {
            "query": query,
            "results": [],
            "total_found": 0,
            "error": str(e),
            "source": "DuckDuckGo",
        }


def test_duckduckgo_search():
    """测试 DuckDuckGo 搜索"""
    rich_print("🧪 测试 DuckDuckGo 搜索功能", RichMessageType.INFO)

    # 创建 Agent
    agent = ChatAgent(mode=ChatMode.AUTO, system="你是一个搜索助手，帮助用户搜索信息。")

    # 注册搜索工具
    agent.register_tools_from_functions(web_search)

    # 测试任务：搜索并总结
    task = "现在几点了？"

    rich_print(f"📋 任务: {task}", RichMessageType.INFO)

    try:
        # 执行任务
        result = agent.run(task=task, max_iterations=3)

        rich_print("✅ 测试完成!", RichMessageType.SUCCESS)
        rich_print(f"状态: {result['status']}", RichMessageType.SYSTEM)
        rich_print(f"轮次: {result['iterations']}", RichMessageType.SYSTEM)
        rich_print(f"用时: {result['execution_time']:.2f}s", RichMessageType.SYSTEM)
        rich_print(f"搜索结果: {result['execution_log']}", RichMessageType.SUCCESS)

        return True

    except Exception as e:
        rich_print(f"❌ 测试失败: {str(e)}", RichMessageType.ERROR)
        import traceback

        rich_print(f"错误详情: {traceback.format_exc()}", RichMessageType.ERROR)
        return False


if __name__ == "__main__":
    success = test_duckduckgo_search()
    if success:
        rich_print("🎉 DuckDuckGo 搜索测试通过!", RichMessageType.SUCCESS)
    else:
        rich_print("💥 DuckDuckGo 搜索测试失败!", RichMessageType.ERROR)
