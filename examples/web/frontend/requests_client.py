#!/usr/bin/env python3
"""
MengLong API测试脚本
这个脚本使用requests库发送HTTP请求，测试MengLong的API服务
"""

import os
import json
import argparse
from enum import Enum
import requests
from typing import List, Dict, Any, Optional, Union
import time


# 服务器URL配置
SERVER_URL = "http://localhost:8000"


class ModelID(str, Enum):
    CLAUDE_3_7_SONNET = "Claude-3.7-Sonnet"
    DEEPSEEK_R1_V1 = "us.deepseek.r1-v1:0"
    DEEPSEEK_REASONER = "deepseek-reasoner"
    DEEPSEEK_CHAT = "deepseek-chat"
    GPT_4O = "gpt-4o"
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
    AMAZON_NOVA_PRO = "us.amazon.nova-pro-v1:0"
    ANTHROPIC_CLAUDE_3_5 = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    ANTHROPIC_CLAUDE_3_7 = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    COHERE_EMBED = "cohere.embed-multilingual-v3"


def print_response(response, is_stream=False):
    """打印API响应"""
    if is_stream:
        print("流式响应内容:")
        for chunk in response.iter_lines():
            if chunk:
                print(chunk.decode("utf-8"))
    else:
        print(f"状态码: {response.status_code}")
        try:
            # 尝试格式化JSON输出
            json_response = response.json()
            print("响应:")
            print(json.dumps(json_response, ensure_ascii=False, indent=2))
        except:
            print("响应内容:")
            print(response.text)


def test_get_models():
    """测试获取可用模型列表"""
    print("\n正在测试: 获取可用模型列表")
    response = requests.get(f"{SERVER_URL}/api/models")
    print_response(response)


def test_chat(message, model_id=ModelID.CLAUDE_3_7_SONNET, stream=False):
    """测试基础聊天API"""
    print(f"\n正在测试: 基础聊天API (model_id={model_id})")

    messages = [{"role": "user", "content": message}]
    data = {"messages": messages, "model_id": model_id, "stream": stream}

    headers = {"Content-Type": "application/json"}

    if stream:
        print("注意: 流式API将逐行输出响应")
        response = requests.post(
            f"{SERVER_URL}/api/chat", json=data, headers=headers, stream=True
        )
        print_response(response, is_stream=True)
    else:
        response = requests.post(f"{SERVER_URL}/api/chat", json=data, headers=headers)
        print_response(response)


def test_agent_chat(role_id, message, model_id=ModelID.DEEPSEEK_REASONER, stream=False):
    """测试角色扮演聊天API"""
    print(f"\n正在测试: 角色扮演聊天API (role_id={role_id})")

    data = {
        "role_id": role_id,
        "messages": message,
        "model_id": model_id,
        "stream": stream,
    }

    headers = {"Content-Type": "application/json"}

    if stream:
        response = requests.post(
            f"{SERVER_URL}/api/agent/chat", json=data, headers=headers, stream=True
        )
        print_response(response, is_stream=True)
    else:
        response = requests.post(
            f"{SERVER_URL}/api/agent/chat", json=data, headers=headers
        )
        print_response(response)


def test_agent_plan():
    """测试获取代理计划"""
    print("\n正在测试: 获取代理计划")
    response = requests.get(f"{SERVER_URL}/api/agent/plan")
    print_response(response)


def test_npc_chat(role_config, message, clear_memory=False):
    """测试NPC聊天API"""
    print("\n正在测试: NPC聊天API")

    data = {"role_config": role_config, "message": message}

    headers = {"Content-Type": "application/json"}
    url = f"{SERVER_URL}/api/agent/npc"

    if clear_memory:
        url += "?clear_memory=true"

    response = requests.post(url, json=data, headers=headers)
    print_response(response)


def test_agent_to_agent(active_role, passive_role, topic, memory_space="memory"):
    """测试角色对话API"""
    print("\n正在测试: 角色对话API")

    data = {
        "active_role": active_role,
        "passive_role": passive_role,
        "topic": topic,
        "memory_space": memory_space,
    }

    headers = {"Content-Type": "application/json"}

    print("注意: ATA API使用流式响应，响应将逐行输出")
    response = requests.post(
        f"{SERVER_URL}/api/agent/ata", json=data, headers=headers, stream=True
    )

    print_response(response, is_stream=True)


def test_vector_store(
    collection_name="knowledge_base", documents=None, query=None, top_k=3
):
    """测试向量数据库API"""
    print("\n正在测试: 向量数据库API")

    data = {
        "collection_name": collection_name,
        "documents": documents or [],
        "query": query,
        "top_k": top_k,
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(
        f"{SERVER_URL}/api/vectorstore", json=data, headers=headers
    )

    print_response(response)


def test_rag(question, collection_name="knowledge_base"):
    """测试RAG API"""
    print("\n正在测试: RAG API")

    data = {"question": question, "collection_name": collection_name}

    headers = {"Content-Type": "application/json"}

    response = requests.post(f"{SERVER_URL}/api/rag", json=data, headers=headers)

    print_response(response)


def main():
    parser = argparse.ArgumentParser(description="MengLong API测试工具")
    parser.add_argument("--url", default=SERVER_URL, help="服务器URL")
    parser.add_argument(
        "--test",
        choices=[
            "all",
            "models",
            "chat",
            "agent",
            "plan",
            "npc",
            "ata",
            "vector",
            "rag",
        ],
        default="all",
        help="要运行的测试",
    )

    args = parser.parse_args()
    global SERVER_URL
    SERVER_URL = args.url

    if args.test in ["all", "models"]:
        test_get_models()

    if args.test in ["all", "chat"]:
        test_chat("你好，请介绍一下MengLong框架的主要功能")

    if args.test in ["all", "agent"]:
        test_agent_chat("js_st_mem", "你好，你是谁？请简单介绍一下自己。")

    if args.test in ["all", "plan"]:
        test_agent_plan()

    if args.test in ["all", "npc"]:
        sample_role_config = {
            "id": "game_npc",
            "role_system": "你是一个游戏中的NPC角色，名叫小明。你是一位年轻的冒险者，性格开朗。",
            "role_info": {"name": "小明", "age": "20", "occupation": "冒险者"},
            "role_var": {"mood": "happy", "energy": "high"},
        }
        test_npc_chat(sample_role_config, "你好，请问你是谁？")

    if args.test in ["all", "ata"]:
        active_role = {
            "id": "Alice",
            "role_system": "你是Alice，一个热爱科技的年轻人。",
            "role_info": {"name": "Alice", "age": "25", "interests": "AI, 编程"},
        }
        passive_role = {
            "id": "Bob",
            "role_system": "你是Bob，一个经验丰富的软件工程师。",
            "role_info": {"name": "Bob", "age": "35", "occupation": "软件工程师"},
        }
        test_agent_to_agent(active_role, passive_role, "讨论人工智能的未来")

    if args.test in ["all", "vector"]:
        # 先添加文档
        documents = [
            "MengLong是一个强大的AI框架，支持多种大型语言模型。",
            "MengLong框架提供了角色扮演、RAG、工具调用等多种功能。",
            "向量数据库是MengLong框架的重要组件，用于存储和检索文本嵌入。",
        ]
        test_vector_store(documents=documents)

        # 然后查询
        time.sleep(1)  # 等待向量插入完成
        test_vector_store(query="MengLong框架有哪些功能？")

    if args.test in ["all", "rag"]:
        test_rag("请介绍一下向量数据库的作用")


if __name__ == "__main__":
    main()
