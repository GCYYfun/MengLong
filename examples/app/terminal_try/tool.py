import subprocess
import shlex
import time
from typing import Any, Dict, List, Optional

from json import JSONDecodeError

import requests
from menglong.agents.component.tool_manager import tool
from menglong.ml_model.schema import user
from menglong import Model
from menglong.utils.log import print_message, print_json, MessageType
import json


@tool
def terminal_command(command_str):
    """
    执行字符串形式的命令行，并捕获输出

    参数:
        command_str (str): 完整的命令行字符串

    返回:
        dict: 包含命令执行结果的字典，包括退出码、输出内容等
    """
    try:
        # 使用shlex分割命令字符串（处理引号/空格等特殊字符）
        command_list = shlex.split(command_str)

        # 启动子进程并捕获输出
        process = subprocess.Popen(
            command_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,  # 分别捕获标准输出和错误输出
            text=True,  # 返回字符串而非字节
            universal_newlines=True,
        )

        # 获取输出
        stdout, stderr = process.communicate()

        # 打印输出供实时查看
        if stdout:
            print("STDOUT:")
            print(stdout)
        if stderr:
            print("STDERR:")
            print(stderr)

        # result = {
        #     "command": command_str,
        #     "exit_code": process.returncode,
        #     "stdout": stdout,
        #     "stderr": stderr,
        #     "success": process.returncode == 0,
        #     "output": stdout if stdout else stderr,  # 主要输出内容
        # }
        result = stdout if stdout else stderr

        return result

    except FileNotFoundError:
        error_msg = f"错误：找不到命令或可执行文件 '{command_list[0]}'"
        print(error_msg)
        return {
            "command": command_str,
            "exit_code": 127,
            "stdout": "",
            "stderr": error_msg,
            "success": False,
            "output": error_msg,
        }
    except Exception as e:
        error_msg = f"执行命令时发生错误: {str(e)}"
        print(error_msg)
        return {
            "command": command_str,
            "exit_code": 1,
            "stdout": "",
            "stderr": error_msg,
            "success": False,
            "output": error_msg,
        }


@tool
def plan_task(description: str, tools: Dict) -> Dict:
    """LLM生成详细执行计划"""
    model = Model()
    available_tools = [name for name, tool in tools.items()]
    for name, tool in tools.items():
        if not tool.get("enabled", True):
            continue
        if tool.get("type") == "function":
            model.register_tool(
                name=name,
                function=tool["function"],
                description=tool.get("description", ""),
                **tool.get("kwargs", {}),
            )
        elif tool.get("type") == "command":
            model.register_tool(
                name=name,
                command=tool["command"],
                description=tool.get("description", ""),
            )
    prompt = f"""
为任务制定详细的执行计划：

任务：{description}

当前可用的工具: {available_tools}

要求：
如果是简单任务(simple)
    - 直接直接执行，获得结果，无需规划。
如果是复杂任务(complex)
    1. 分解为具体的子任务
    2. 明确每个子任务的依赖关系
    3. 指定执行工具
    4. 预期输出和成功标准要与任务目标和相关依赖任务保持一致

父任务子任务的划分按照以下规则:
    1. 根据模块的功能划分，为了明确每个子任务的职责
    2. 根据任务的输入输出关系划分,确保无缺无漏完成父任务
    3. 与任务的依赖关系正交,不以依赖关系为主,以功能划分为主

返回JSON格式:
{{
  "task_tag": "任务tag",
  "task_type": "complex/simple",  # 任务类型
  "description": "任务的目的描述",
  "subtasks": [
    {{
      "task_tag": "任务tag",
      "task_type": "simple/complex",
      "description": "任务的详细描述",
      "dependencies": [],  # 依赖的task_tag列表
      "parent": "父任务的task_tag",
      "tool_require": [],  # 需要的工具列表
      "subtasks": [],  # 子任务列表
      "expected_output": "预期的输出结果描述",
      "success_criteria": "验证任务完成的标准",
    }},
  ],
  "success_criteria": "任务最终目标，量化的结果,整体任务完成标准"
}}

只返回JSON，不要其他解释。
"""
    try:
        start_time = time.time()
        response = model.chat([user(content=prompt)])
        response_text = response.message.content.text
        print_message(
            f"{response_text[:500]}", title="Raw response text"
        )  # 调试输出前500个字符

        # 解析JSON
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        execution_plan = json.loads(response_text)
        print_json(
            execution_plan,
            title="Parsed execution plan subtasks",
        )
        end_time = time.time()
        print_message(f"Execution time: {end_time - start_time:.2f} seconds")
        return execution_plan

    except JSONDecodeError as e:
        print_message(f"JSON decode error: {e}")
        raise ValueError(f"Failed to parse execution plan JSON: {e}")
    except Exception as e:
        raise ValueError(f"Failed to generate execution plan: {e}") from e


@tool
def web_search(query: str, max_results: int = 3) -> Dict[str, Any]:
    """使用DuckDuckGo进行真实的网络搜索"""
    try:
        from duckduckgo_search import DDGS

        print_message(f"🔍 正在搜索: {query}")

        results = []
        with DDGS() as ddgs:
            # 执行搜索，限制结果数量
            search_results = list(ddgs.text(query, max_results=max_results))

            print_json(search_results, title="Raw search results")
            for i, result in enumerate(search_results):
                results.append(
                    {
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                        "snippet": result.get("body", ""),
                        "relevance": 1.0 - (i * 0.1),  # 按顺序递减相关性
                    }
                )

        print_message(f"✅ 搜索完成，找到 {len(results)} 个结果", MessageType.SUCCESS)

        return {
            "query": query,
            "results": results,
            "total_found": len(results),
            "search_time": time.time(),
            "source": "DuckDuckGo",
        }

    except Exception as e:
        print_message(f"❌ 搜索出错: {str(e)}", MessageType.ERROR)
        return {
            "query": query,
            "results": [],
            "total_found": 0,
            "error": str(e),
            "source": "DuckDuckGo",
        }


@tool
def brave_web_search(query: str, max_results: int = 1) -> Dict[str, Any]:
    """
    使用Brave Search API进行真实的网络搜索

    Args:
        query (str): 搜索按钮
        max_results (int, optional): 最大返回结果数， Defaults to 1.

    Returns:
        Dict[str, Any]: 搜索图像分类
    """
    # Brave Search API URL
    url = "https://api.search.brave.com/res/v1/web/search"

    # 设置请求头
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": "<YOUR_API_KEY>",
    }

    # 设置请求参数
    params = {"q": query, "limit": max_results}

    # try:
    # 发送请求
    response = requests.get(url, headers=headers, params=params)
    print_message(f"🔍 正在搜索: {query}")
    # 检查响应状态码
    if response.status_code == 200:
        # 解析JSON响应
        result = response.json()
        print_json(result, title="Raw search results")

        # 提取搜索结果
        if "web" in result and "results" in result["web"]:
            results = result["web"]["results"]
            return {"status": "success", "results": results[:max_results]}
        else:
            return {"status": "error", "message": "No results found"}
    else:
        return {
            "status": "error",
            "message": f"API request failed with status code {response.status_code}",
        }

    # except requests.exceptions.RequestException as e:
    #     return {"status": "error", "message": f"Request error: {str(e)}"}
