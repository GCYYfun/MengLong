from typing import List, Dict, Any, Optional, Literal
from enum import Enum
import json
from menglong.agents import ChatAgent, tool


# 测试1：完全没有 docstring
@tool
def get_weather_auto(location: str, unit: Literal["celsius", "fahrenheit"] = "celsius"):
    """获取天气信息"""
    return {
        "location": location,
        "temperature": 22 if unit == "celsius" else 72,
        "unit": unit,
        "description": "Sunny",
    }


tools = [get_weather_auto]
print(type(get_weather_auto))
print(get_weather_auto._tool_info.name)
print(get_weather_auto._tool_info.description)
print(get_weather_auto._tool_info.parameters)

agent = ChatAgent(
    system="你是一个智能助手，可以使用工具来回答问题",
)

# res = agent.chat(
#     "今天北京的天气怎么样？",
#     tools=tools,
# )
# print(f"Agent: {res}")


res = agent.run("今天北京的天气怎么样？")  # , tools=tools)

print(f"Agent Run: {res}")
