#!/usr/bin/env python3
"""
MengLong API测试脚本
这个脚本提供了多种curl命令示例，用于测试MengLong的API服务
"""

import os
import json
import subprocess
import argparse
from enum import Enum


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


def run_curl(curl_command):
    """执行curl命令并打印结果"""
    print(f"\n执行命令: {curl_command}")
    result = subprocess.run(curl_command, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        try:
            # 尝试格式化JSON输出
            json_response = json.loads(result.stdout)
            print("响应:")
            print(json.dumps(json_response, ensure_ascii=False, indent=2))
        except:
            print("响应:")
            print(result.stdout)
    else:
        print("错误:")
        print(result.stderr)


def test_get_models():
    """测试获取可用模型列表"""
    curl_command = f'curl -X GET "{SERVER_URL}/api/models"'
    run_curl(curl_command)


def test_chat(message, model_id=ModelID.CLAUDE_3_7_SONNET, stream=False):
    """测试基础聊天API"""
    messages = [{"role": "user", "content": message}]
    data = {"messages": messages, "model_id": model_id, "stream": stream}

    curl_command = f"""
    curl -X POST "{SERVER_URL}/api/chat" \\
    -H "Content-Type: application/json" \\
    -d '{json.dumps(data, ensure_ascii=False)}'
    """

    if stream:
        print("注意: 流式API在此脚本中无法正确显示，请在浏览器或其他工具中测试")

    run_curl(curl_command)


def test_agent_chat(role_id, message, model_id=ModelID.DEEPSEEK_REASONER, stream=False):
    """测试角色扮演聊天API"""
    data = {
        "role_id": role_id,
        "messages": message,
        "model_id": model_id,
        "stream": stream,
    }

    curl_command = f"""
    curl -X POST "{SERVER_URL}/api/agent/chat" \\
    -H "Content-Type: application/json" \\
    -d '{json.dumps(data, ensure_ascii=False)}'
    """

    run_curl(curl_command)


def test_agent_plan():
    """测试获取代理计划"""
    curl_command = f'curl -X GET "{SERVER_URL}/api/agent/plan"'
    run_curl(curl_command)


def test_npc_chat(role_config, message, clear_memory=False):
    """测试NPC聊天API"""
    data = {"role_config": role_config, "message": message}

    query_param = "?clear_memory=true" if clear_memory else ""

    curl_command = f"""
    curl -X POST "{SERVER_URL}/api/agent/npc{query_param}" \\
    -H "Content-Type: application/json" \\
    -d '{json.dumps(data, ensure_ascii=False)}'
    """

    run_curl(curl_command)


def test_agent_to_agent(active_role, passive_role, topic, memory_space="memory"):
    """测试角色对话API"""
    data = {
        "active_role": active_role,
        "passive_role": passive_role,
        "topic": topic,
        "memory_space": memory_space,
    }

    curl_command = f"""
    curl -X POST "{SERVER_URL}/api/agent/ata" \\
    -H "Content-Type: application/json" \\
    -d '{json.dumps(data, ensure_ascii=False)}'
    """

    print("注意: ATA API使用流式响应，在此脚本中可能无法正确显示")
    run_curl(curl_command)


def test_vector_store(
    collection_name="knowledge_base", documents=None, query=None, top_k=3
):
    """测试向量数据库API"""
    data = {
        "collection_name": collection_name,
        "documents": documents or [],
        "query": query,
        "top_k": top_k,
    }

    curl_command = f"""
    curl -X POST "{SERVER_URL}/api/vectorstore" \\
    -H "Content-Type: application/json" \\
    -d '{json.dumps(data, ensure_ascii=False)}'
    """

    run_curl(curl_command)


def test_rag(question, collection_name="knowledge_base"):
    """测试RAG API"""
    data = {"question": question, "collection_name": collection_name}

    curl_command = f"""
    curl -X POST "{SERVER_URL}/api/rag" \\
    -H "Content-Type: application/json" \\
    -d '{json.dumps(data, ensure_ascii=False)}'
    """

    run_curl(curl_command)


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
        test_vector_store(query="MengLong框架有哪些功能？")

    if args.test in ["all", "rag"]:
        test_rag("请介绍一下向量数据库的作用")


if __name__ == "__main__":
    main()
