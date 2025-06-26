import subprocess
import shlex
import time
import os
import glob
import yaml
import math
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


@tool
def recall_experience(query: str) -> str:
    """
    使用RAG方式回忆相关经验

    参数:
        query (str): 思考的内容或经验查询

    返回:
        str: 检索到的相关经验内容
    """
    print_message(f"💭 正在检索相关经验: {query}")

    try:
        # 初始化模型
        model = Model()

        # 经验库文件路径
        experience_file = (
            "/Users/own/Workspace/MengLong/examples/app/terminal_try/experience.yaml"
        )

        # 检查经验库文件是否存在
        if not os.path.exists(experience_file):
            print_message("经验库文件不存在，返回空结果")
            return "暂无相关经验记录。"

        # 读取经验库
        try:
            with open(experience_file, "r", encoding="utf-8") as f:
                experience_data = yaml.safe_load(f) or {}
        except Exception as e:
            print_message(f"读取经验库失败: {e}")
            return "无法读取经验库。"

        experiences = experience_data.get("experiences", [])
        if not experiences:
            return "经验库为空，暂无相关经验记录。"

        # 使用向量搜索找到最相关的经验
        top_experiences = _vector_search(query, experiences, model)

        if not top_experiences:
            # 降级为关键词搜索
            top_experiences = _keyword_search_experiences(query, experiences)

        if not top_experiences:
            return "未找到相关的经验记录。您可能需要积累更多相关经验。"

        # 使用LLM整合和总结检索到的经验
        context_prompt = f"""
基于以下查询和检索到的相关经验，提供有用的建议和指导：

查询：{query}

相关经验记录：
"""

        for i, item in enumerate(top_experiences):
            exp = item["experience"]
            similarity = item.get("similarity", 0)
            context_prompt += f"""
经验 {i+1} (相关度: {similarity:.2f}):
标题: {exp.get('title', '未知')}
分类: {exp.get('category', '未知')}
摘要: {exp.get('summary', '无摘要')}
关键点: {', '.join(exp.get('details', {}).get('key_points', []))}
适用场景: {', '.join(exp.get('details', {}).get('applicable_scenarios', []))}
注意事项: {', '.join(exp.get('details', {}).get('pitfalls', []))}

"""

        context_prompt += """
请基于这些经验记录，为用户的查询提供：
1. 直接相关的解决方案或建议
2. 需要注意的关键点和陷阱
3. 适用的最佳实践
4. 如果经验不够完全匹配，请说明哪些部分可以参考

返回结构化的建议，要实用和具体。
"""

        start_time = time.time()
        response = model.chat([user(content=context_prompt)])
        final_advice = response.message.content.text

        end_time = time.time()
        print_message(
            f"✅ 经验检索完成，耗时: {end_time - start_time:.2f} 秒",
            MessageType.SUCCESS,
        )
        print_message(
            f"找到 {len(top_experiences)} 条相关经验", title="Retrieved Experience"
        )

        return final_advice

    except Exception as e:
        error_msg = f"经验检索失败: {str(e)}"
        print_message(f"❌ {error_msg}", MessageType.ERROR)
        return f"经验检索遇到问题: {error_msg}"


def _vector_search(query: str, experiences: List[Dict], model: Model) -> List[Dict]:
    """使用 menglong 模型进行向量相似度搜索"""
    try:
        # 生成查询向量
        query_embedding = model.embed([query])
        if not query_embedding or len(query_embedding.embeddings) == 0:
            print_message("查询向量化失败，降级为关键词搜索")
            return []

        query_vector = query_embedding.embeddings
        relevant_items = []

        # 计算与每个经验的相似度
        for exp in experiences:
            if "embedding" not in exp:
                continue  # 跳过没有向量的经验

            exp_vector = exp["embedding"]
            # 计算余弦相似度
            similarity = _cosine_similarity(query_vector, exp_vector)

            # 相似度阈值为 0.3
            if similarity > 0.3:
                relevant_items.append(
                    {"similarity": float(similarity), "experience": exp}
                )

        # 按相似度排序，取前3个
        relevant_items.sort(key=lambda x: x["similarity"], reverse=True)
        print_message(f"向量搜索找到 {len(relevant_items)} 条相关经验")
        return relevant_items[:3]

    except Exception as e:
        print_message(f"向量搜索失败: {e}")
        return []


def _keyword_search_experiences(query: str, experiences: List[Dict]) -> List[Dict]:
    """关键词匹配搜索"""
    query_keywords = query.lower().split()
    matches = []

    for exp in experiences:
        # 构建搜索文本
        searchable_text = f"{exp.get('title', '')} {exp.get('summary', '')} {' '.join(exp.get('tags', []))}".lower()

        # 计算关键词匹配度
        match_count = sum(1 for keyword in query_keywords if keyword in searchable_text)
        if match_count > 0:
            matches.append(
                {"similarity": match_count / len(query_keywords), "experience": exp}
            )

    # 按匹配度排序，取前3个
    matches.sort(key=lambda x: x["similarity"], reverse=True)
    print_message(f"关键词搜索找到 {len(matches)} 条相关经验")
    return matches[:3]


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """计算两个向量的余弦相似度"""
    try:
        # 计算点积
        dot_product = sum(a * b for a, b in zip(vec1, vec2))

        # 计算向量长度
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(a * a for a in vec2))

        # 避免除零
        if norm1 == 0 or norm2 == 0:
            return 0.0

        # 计算余弦相似度
        return dot_product / (norm1 * norm2)
    except Exception:
        return 0.0


@tool
def summarize_and_save_experience(experience: str) -> str:
    """
    总结并保存实践经验到 YAML 文件

    参数:
        experience (str): 要保存的实践经验内容

    返回:
        str: 保存结果的确认信息
    """
    print_message(f"💾 正在总结并保存实践经验...")

    try:
        # 初始化模型
        model = Model()

        # 构建总结提示词
        summary_prompt = f"""
请对以下实践经验进行结构化总结和提炼：

原始经验内容：
{experience}

请按以下格式总结：
{{
  "title": "经验标题（简洁明了）",
  "category": "经验分类（如：开发技巧、问题解决、最佳实践等）",
  "tags": ["标签1", "标签2", "标签3"],
  "summary": "核心要点总结",
  "details": {{
    "problem": "遇到的问题或场景",
    "solution": "解决方案或方法",
    "key_points": ["关键要点1", "关键要点2"],
    "pitfalls": ["注意事项或陷阱"],
    "applicable_scenarios": ["适用场景1", "适用场景2"]
  }},
  "difficulty": "难度等级（简单/中等/困难）",
  "usefulness": "实用性评分（1-5分）"
}}

只返回JSON格式，不要其他解释。
"""

        start_time = time.time()
        response = model.chat([user(content=summary_prompt)])
        summary_text = response.message.content.text

        # 解析JSON
        if summary_text.startswith("```json"):
            summary_text = summary_text[7:]
        if summary_text.endswith("```"):
            summary_text = summary_text[:-3]

        try:
            structured_experience = json.loads(summary_text)
            print_json(structured_experience, title="Structured Experience Summary")

            # 经验库文件路径
            experience_file = "/Users/own/Workspace/MengLong/examples/app/terminal_try/experience.yaml"

            # 读取现有经验库
            experience_data = {"experiences": []}
            if os.path.exists(experience_file):
                try:
                    with open(experience_file, "r", encoding="utf-8") as f:
                        experience_data = yaml.safe_load(f) or {"experiences": []}
                except Exception as e:
                    print_message(f"读取现有经验库失败: {e}")

            # 添加元数据
            experience_id = f"exp_{int(time.time())}"
            structured_experience["id"] = experience_id
            structured_experience["created_at"] = time.time()
            structured_experience["raw_content"] = experience

            # 生成搜索文本用于后续检索
            searchable_text = f"{structured_experience.get('title', '')} {structured_experience.get('summary', '')} {' '.join(structured_experience.get('tags', []))}"

            # 使用 menglong 的 embed 函数生成向量
            try:
                embedding = model.embed([searchable_text])
                if embedding and len(embedding.embeddings) > 0:
                    structured_experience["embedding"] = embedding.embeddings
                    print_message("✅ 经验向量化成功")
                else:
                    print_message("⚠️ 向量化失败，将不支持语义搜索")
            except Exception as e:
                print_message(f"⚠️ 向量化失败: {e}")

            # 添加到经验库
            if "experiences" not in experience_data:
                experience_data["experiences"] = []
            experience_data["experiences"].append(structured_experience)

            # 保存到 YAML 文件
            with open(experience_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    experience_data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                )

            end_time = time.time()
            print_message(
                f"✅ 经验总结和保存完成，耗时: {end_time - start_time:.2f} 秒",
                MessageType.SUCCESS,
            )
            print_message(f"保存位置: {experience_file}", title="Experience Saved")

            return f"实践经验已成功总结并保存。经验ID: {experience_id}，标题: {structured_experience.get('title', '未知')}"

        except JSONDecodeError as e:
            print_message(f"JSON解析错误: {e}")
            # 降级处理：直接保存原始内容
            fallback_experience = {
                "id": f"raw_{int(time.time())}",
                "title": "原始经验记录",
                "category": "未分类",
                "tags": ["原始记录"],
                "summary": (
                    experience[:200] + "..." if len(experience) > 200 else experience
                ),
                "raw_content": experience,
                "created_at": time.time(),
                "details": {
                    "problem": "待整理",
                    "solution": "待整理",
                    "key_points": ["原始记录待整理"],
                    "pitfalls": [],
                    "applicable_scenarios": [],
                },
                "difficulty": "未知",
                "usefulness": "未评分",
            }

            # 读取现有经验库并添加
            experience_data = {"experiences": []}
            if os.path.exists(experience_file):
                try:
                    with open(experience_file, "r", encoding="utf-8") as f:
                        experience_data = yaml.safe_load(f) or {"experiences": []}
                except:
                    pass

            experience_data["experiences"].append(fallback_experience)

            with open(experience_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    experience_data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                )

            return f"经验保存成功（原始格式），ID: {fallback_experience['id']}"

    except Exception as e:
        error_msg = f"经验总结和保存失败: {str(e)}"
        print_message(f"❌ {error_msg}", MessageType.ERROR)
        return f"经验保存遇到问题: {error_msg}"


@tool
def abstract_experience(domain: str = "", pattern_type: str = "all") -> str:
    """
    从经验库中抽象化经验模式和通用规律

    参数:
        domain (str): 要抽象的领域或主题（如："编程调试", "项目管理", "问题解决"等）
        pattern_type (str): 抽象模式类型 ("all", "success_patterns", "failure_patterns", "best_practices")

    返回:
        str: 抽象化的经验模式和规律总结
    """
    if domain == "":
        domain = "全部"
    print_message(f"🧠 正在抽象 '{domain}' 领域的经验模式，类型: {pattern_type}")

    try:
        # 初始化模型
        model = Model()

        # 经验库文件路径
        experience_file = (
            "/Users/own/Workspace/MengLong/examples/app/terminal_try/experience.yaml"
        )

        # 检查经验库文件是否存在
        if not os.path.exists(experience_file):
            return "经验库文件不存在，无法进行经验抽象。"

        # 读取经验库
        try:
            with open(experience_file, "r", encoding="utf-8") as f:
                experience_data = yaml.safe_load(f) or {}
        except Exception as e:
            print_message(f"读取经验库失败: {e}")
            return "无法读取经验库文件。"

        experiences = experience_data.get("experiences", [])
        if not experiences:
            return "经验库为空，无法进行经验抽象。"

        if domain == "全部":
            print_message("抽象全部领域的经验")
            # 如果是全部领域，则不进行领域筛选
            relevant_experiences = experiences
        else:
            print_message(f"抽象领域: {domain}")
            # 根据领域筛选相关经验
            relevant_experiences = _filter_experiences_by_domain(
                domain, experiences, model
            )

        if not relevant_experiences:
            return f"在 '{domain}' 领域未找到相关经验，无法进行抽象。"

        print_message(f"找到 {len(relevant_experiences)} 条相关经验进行抽象")

        # 构建抽象化提示词
        abstraction_prompt = _build_abstraction_prompt(
            domain, pattern_type, relevant_experiences
        )

        # 使用LLM进行经验抽象
        start_time = time.time()
        response = model.chat([user(content=abstraction_prompt)])
        abstracted_patterns = response.message.content.text

        end_time = time.time()
        print_message(
            f"✅ 经验抽象完成，耗时: {end_time - start_time:.2f} 秒",
            MessageType.SUCCESS,
        )

        # 可选：将抽象结果保存为新的高级经验
        _save_abstract_pattern(
            domain, pattern_type, abstracted_patterns, len(relevant_experiences)
        )

        return abstracted_patterns

    except Exception as e:
        error_msg = f"经验抽象失败: {str(e)}"
        print_message(f"❌ {error_msg}", MessageType.ERROR)
        return f"经验抽象遇到问题: {error_msg}"


def _filter_experiences_by_domain(
    domain: str, experiences: List[Dict], model: Model
) -> List[Dict]:
    """根据领域筛选相关经验"""
    try:
        # 生成领域查询向量
        domain_embedding = model.embed([domain])
        if not domain_embedding or len(domain_embedding.embeddings) == 0:
            # 降级为关键词匹配
            return _filter_by_keywords(domain, experiences)

        domain_vector = domain_embedding.embeddings
        relevant_experiences = []

        # 计算每个经验与领域的相关性
        for exp in experiences:
            if "embedding" not in exp:
                continue

            similarity = _cosine_similarity(domain_vector, exp["embedding"])
            if similarity > 0.25:  # 较低的阈值，包含更多相关经验
                relevant_experiences.append(
                    {"experience": exp, "relevance": similarity}
                )

        # 按相关性排序
        relevant_experiences.sort(key=lambda x: x["relevance"], reverse=True)
        return [item["experience"] for item in relevant_experiences]

    except Exception as e:
        print_message(f"向量筛选失败: {e}")
        return _filter_by_keywords(domain, experiences)


def _filter_by_keywords(domain: str, experiences: List[Dict]) -> List[Dict]:
    """关键词筛选相关经验"""
    domain_keywords = domain.lower().split()
    relevant_experiences = []

    for exp in experiences:
        searchable_text = f"{exp.get('title', '')} {exp.get('summary', '')} {exp.get('category', '')} {' '.join(exp.get('tags', []))}".lower()

        # 计算关键词匹配度
        match_count = sum(
            1 for keyword in domain_keywords if keyword in searchable_text
        )
        if match_count > 0:
            relevant_experiences.append(exp)

    print_message(f"关键词筛选找到 {len(relevant_experiences)} 条经验")
    return relevant_experiences


def _build_abstraction_prompt(
    domain: str, pattern_type: str, experiences: List[Dict]
) -> str:
    """构建经验抽象的提示词"""

    base_prompt = f"""
请对以下 '{domain}' 领域的经验进行深度抽象和模式提取。

领域: {domain}
抽象类型: {pattern_type}
经验数量: {len(experiences)}

相关经验数据:
"""

    # 添加经验内容
    for i, exp in enumerate(experiences[:10]):  # 限制最多10条经验
        base_prompt += f"""
经验 {i+1}:
- 标题: {exp.get('title', '未知')}
- 分类: {exp.get('category', '未知')}
- 问题: {exp.get('details', {}).get('problem', '无')}
- 解决方案: {exp.get('details', {}).get('solution', '无')}
- 关键点: {', '.join(exp.get('details', {}).get('key_points', []))}
- 陷阱: {', '.join(exp.get('details', {}).get('pitfalls', []))}
- 适用场景: {', '.join(exp.get('details', {}).get('applicable_scenarios', []))}
- 难度: {exp.get('difficulty', '未知')}

"""

    # 根据抽象类型添加特定指导
    if pattern_type == "success_patterns":
        specific_prompt = """
请重点提取成功模式和规律：
1. 成功解决问题的共同方法和策略
2. 高效解决方案的共同特征
3. 成功案例中的关键决策点
4. 可复用的成功模式和框架
"""
    elif pattern_type == "failure_patterns":
        specific_prompt = """
请重点提取失败模式和陷阱：
1. 常见的错误和陷阱
2. 容易忽视的风险点
3. 失败案例的共同特征
4. 需要避免的行为模式
"""
    elif pattern_type == "best_practices":
        specific_prompt = """
请重点提取最佳实践：
1. 经过验证的优秀做法
2. 效率最高的工作方法
3. 通用的解决框架
4. 标准化的操作流程
"""
    else:  # "all"
        specific_prompt = """
请进行全面的经验抽象：
1. 成功模式和规律
2. 失败模式和陷阱
3. 最佳实践和标准流程
4. 通用原则和方法论
"""

    final_prompt = (
        base_prompt
        + specific_prompt
        + """

请按以下结构输出抽象结果：

## 核心模式识别
[识别出的主要模式和规律]

## 通用原则
[提取的通用原则和方法论]

## 决策框架
[形成的决策和判断框架]

## 实践指南
[具体的实践指导建议]

## 风险预警
[需要注意的风险和陷阱]

## 适用条件
[这些模式和原则的适用范围和条件]

要求：
- 抽象层次要高于具体经验，形成可复用的模式
- 要有实用价值，能指导未来的类似问题
- 保持逻辑性和结构性
- 突出共性，淡化个性
"""
    )

    return final_prompt


def _save_abstract_pattern(
    domain: str, pattern_type: str, abstracted_content: str, source_count: int
):
    """将抽象模式保存为高级经验"""
    try:
        # 构建抽象经验记录
        abstract_experience = {
            "id": f"abstract_{int(time.time())}",
            "title": f"{domain}领域-{pattern_type}抽象模式",
            "category": "抽象模式",
            "tags": [domain, pattern_type, "抽象经验", "模式"],
            "summary": f"从{source_count}条经验中抽象出的{domain}领域{pattern_type}模式",
            "details": {
                "problem": f"{domain}领域的通用问题模式",
                "solution": f"抽象化的解决方案和方法论",
                "key_points": [
                    f"基于{source_count}条经验的抽象",
                    f"{pattern_type}模式",
                    "高级经验",
                ],
                "pitfalls": ["抽象层次较高，需要结合具体情况应用"],
                "applicable_scenarios": [f"{domain}相关的各种场景"],
            },
            "difficulty": "中等",
            "usefulness": "5",
            "created_at": time.time(),
            "raw_content": abstracted_content,
            "source_experiences_count": source_count,
            "abstraction_type": pattern_type,
        }

        # 读取现有经验库
        experience_file = (
            "/Users/own/Workspace/MengLong/examples/app/terminal_try/experience.yaml"
        )
        experience_data = {"experiences": []}
        if os.path.exists(experience_file):
            with open(experience_file, "r", encoding="utf-8") as f:
                experience_data = yaml.safe_load(f) or {"experiences": []}

        # 添加抽象经验
        experience_data["experiences"].append(abstract_experience)

        # 保存回文件
        with open(experience_file, "w", encoding="utf-8") as f:
            yaml.dump(
                experience_data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                indent=2,
            )

        print_message(f"✅ 抽象模式已保存为高级经验: {abstract_experience['id']}")

    except Exception as e:
        print_message(f"⚠️ 抽象模式保存失败: {e}")


@tool
def debug_experience_db() -> str:
    """
    调试经验库内容，检查格式和数据

    返回:
        str: 经验库的调试信息
    """
    print_message("🔍 开始调试经验库...")

    try:
        # 经验库文件路径
        experience_file = (
            "/Users/own/Workspace/MengLong/examples/app/terminal_try/experience.yaml"
        )

        # 检查文件是否存在
        if not os.path.exists(experience_file):
            return "❌ 经验库文件不存在"

        # 读取经验库
        with open(experience_file, "r", encoding="utf-8") as f:
            experience_data = yaml.safe_load(f) or {}

        experiences = experience_data.get("experiences", [])

        debug_info = f"""
📊 经验库调试报告
===================

📁 文件路径: {experience_file}
📈 经验总数: {len(experiences)}

"""

        if not experiences:
            debug_info += "⚠️ 经验库为空\n"
            return debug_info

        # 检查每个经验的格式
        for i, exp in enumerate(experiences):
            debug_info += f"""
经验 {i+1}:
  ID: {exp.get('id', 'Missing')}
  标题: {exp.get('title', 'Missing')}
  分类: {exp.get('category', 'Missing')}
  标签: {exp.get('tags', [])}
  向量: {'✅ 存在' if 'embedding' in exp and exp['embedding'] else '❌ 缺失'}
"""
            if "embedding" in exp and exp["embedding"]:
                debug_info += f"  向量维度: {len(exp['embedding'])}\n"

            # 检查必要字段
            required_fields = ["title", "summary", "details"]
            missing_fields = [field for field in required_fields if field not in exp]
            if missing_fields:
                debug_info += f"  ⚠️ 缺失字段: {missing_fields}\n"

        # 统计信息
        has_embedding = sum(
            1 for exp in experiences if "embedding" in exp and exp["embedding"]
        )
        debug_info += f"""
📊 统计信息:
  有向量的经验: {has_embedding}/{len(experiences)}
  向量化率: {has_embedding/len(experiences)*100:.1f}%
"""

        return debug_info

    except Exception as e:
        return f"❌ 调试失败: {str(e)}"


@tool
def test_embedding_functionality() -> str:
    """
    测试 embedding 功能是否正常工作

    返回:
        str: 测试结果
    """
    print_message("🧪 开始测试 embedding 功能...")

    try:
        # 初始化模型
        model = Model()

        # 测试文本
        test_texts = ["这是一个测试文本", "编程调试技巧", "项目管理经验"]

        test_results = []

        for text in test_texts:
            try:
                print_message(f"测试文本: {text}")
                embed_response = model.embed([text])

                if embed_response and hasattr(embed_response, "embeddings"):
                    if len(embed_response.embeddings) > 0:
                        vector = embed_response.embeddings[0]
                        test_results.append(f"✅ '{text}' - 向量维度: {len(vector)}")
                        print_message(f"向量前5个值: {vector[:5]}")
                    else:
                        test_results.append(f"❌ '{text}' - embeddings 列表为空")
                else:
                    test_results.append(f"❌ '{text}' - 没有 embeddings 属性")

            except Exception as e:
                test_results.append(f"❌ '{text}' - 错误: {str(e)}")

        # 测试余弦相似度计算
        if len(test_results) >= 2 and all(
            "✅" in result for result in test_results[:2]
        ):
            try:
                vec1 = model.embed([test_texts[0]]).embeddings[0]
                vec2 = model.embed([test_texts[1]]).embeddings[0]
                similarity = _cosine_similarity(vec1, vec2)
                test_results.append(f"✅ 余弦相似度计算: {similarity:.4f}")
            except Exception as e:
                test_results.append(f"❌ 余弦相似度计算失败: {str(e)}")

        result = "🧪 Embedding 功能测试结果:\n" + "\n".join(test_results)
        return result

    except Exception as e:
        return f"❌ 测试失败: {str(e)}"


def _find_similar_experience_groups(
    experiences: List[Dict], threshold: float, model: Model
) -> List[List[Dict]]:
    """找到相似的经验组"""
    try:
        # 为没有向量的经验生成向量
        for exp in experiences:
            if "embedding" not in exp or not exp["embedding"]:
                searchable_text = f"{exp.get('title', '')} {exp.get('summary', '')} {' '.join(exp.get('tags', []))}"
                try:
                    embed_response = model.embed([searchable_text])
                    if (
                        embed_response
                        and hasattr(embed_response, "embeddings")
                        and len(embed_response.embeddings) > 0
                    ):
                        exp["embedding"] = embed_response.embeddings[0]
                        print_message(
                            f"为经验 '{exp.get('title', 'Unknown')}' 生成向量"
                        )
                except Exception as e:
                    print_message(f"向量生成失败: {exp.get('title', 'Unknown')} - {e}")

        # 计算所有经验之间的相似度
        similar_groups = []
        processed = set()

        for i, exp1 in enumerate(experiences):
            if exp1.get("id") in processed or "embedding" not in exp1:
                continue

            current_group = [exp1]
            processed.add(exp1.get("id"))

            for j, exp2 in enumerate(experiences[i + 1 :], i + 1):
                if exp2.get("id") in processed or "embedding" not in exp2:
                    continue

                # 计算相似度
                similarity = _cosine_similarity(exp1["embedding"], exp2["embedding"])

                if similarity > threshold:
                    current_group.append(exp2)
                    processed.add(exp2.get("id"))
                    print_message(
                        f"发现相似经验: '{exp1.get('title', 'Unknown')}' 与 '{exp2.get('title', 'Unknown')}' 相似度: {similarity:.3f}"
                    )

            if len(current_group) > 1:
                similar_groups.append(current_group)

        return similar_groups

    except Exception as e:
        print_message(f"查找相似经验组失败: {e}")
        return []


def _merge_similar_experiences(experiences: List[Dict], model: Model) -> Dict:
    """合并相似的经验为一条更好的经验"""
    try:
        # 构建合并提示词
        merge_prompt = f"""
请将以下 {len(experiences)} 条相似的经验合并为一条更完整、更优质的经验记录。

相似经验列表:
"""

        for i, exp in enumerate(experiences):
            merge_prompt += f"""
经验 {i+1}:
- 标题: {exp.get('title', '未知')}
- 分类: {exp.get('category', '未知')}
- 标签: {exp.get('tags', [])}
- 摘要: {exp.get('summary', '无摘要')}
- 问题: {exp.get('details', {}).get('problem', '无')}
- 解决方案: {exp.get('details', {}).get('solution', '无')}
- 关键点: {exp.get('details', {}).get('key_points', [])}
- 陷阱: {exp.get('details', {}).get('pitfalls', [])}
- 适用场景: {exp.get('details', {}).get('applicable_scenarios', [])}
- 难度: {exp.get('difficulty', '未知')}
- 实用性: {exp.get('usefulness', '未知')}

"""

        merge_prompt += """
请按以下要求合并:
1. 提取最精准的标题，涵盖所有经验的核心主题
2. 选择最合适的分类
3. 合并所有相关标签，去除重复
4. 综合所有摘要，形成更完整的描述
5. 整合问题描述，覆盖所有场景
6. 合并解决方案，保留最有效的方法
7. 汇总所有关键点，去重并排序
8. 整合所有陷阱和注意事项
9. 扩展适用场景覆盖范围
10. 评估综合难度和实用性

返回JSON格式:
{
  "title": "合并后的标题",
  "category": "最合适的分类",
  "tags": ["合并后的标签列表"],
  "summary": "综合摘要",
  "details": {
    "problem": "整合后的问题描述",
    "solution": "综合解决方案",
    "key_points": ["整合后的关键点列表"],
    "pitfalls": ["合并后的陷阱列表"],
    "applicable_scenarios": ["扩展后的适用场景"]
  },
  "difficulty": "评估后的难度",
  "usefulness": "评估后的实用性"
}

只返回JSON，不要其他解释。
"""

        # 使用LLM合并经验
        response = model.chat([user(content=merge_prompt)])
        merge_text = response.message.content.text

        # 解析JSON
        if merge_text.startswith("```json"):
            merge_text = merge_text[7:]
        if merge_text.endswith("```"):
            merge_text = merge_text[:-3]

        merged_experience = json.loads(merge_text)

        # 添加元数据
        merged_experience["id"] = f"merged_{int(time.time())}"
        merged_experience["created_at"] = time.time()
        merged_experience["merged_from"] = [exp.get("id") for exp in experiences]
        merged_experience["merge_count"] = len(experiences)

        # 生成合并后的原始内容
        raw_content = f"合并自 {len(experiences)} 条经验:\n"
        for exp in experiences:
            raw_content += f"- {exp.get('title', 'Unknown')}\n"
        raw_content += f"\n综合内容: {merged_experience.get('summary', '')}"
        merged_experience["raw_content"] = raw_content

        # 生成新的向量
        searchable_text = f"{merged_experience.get('title', '')} {merged_experience.get('summary', '')} {' '.join(merged_experience.get('tags', []))}"
        try:
            embed_response = model.embed([searchable_text])
            if (
                embed_response
                and hasattr(embed_response, "embeddings")
                and len(embed_response.embeddings) > 0
            ):
                merged_experience["embedding"] = embed_response.embeddings[0]
        except Exception as e:
            print_message(f"合并经验向量化失败: {e}")

        print_message(f"成功合并经验: {merged_experience.get('title', 'Unknown')}")
        return merged_experience

    except Exception as e:
        print_message(f"合并经验失败: {e}")
        return None


@tool
def merge_similar_experiences(
    similarity_threshold: float = 0.7, domain_filter: str = ""
) -> str:
    """
    整理经验库，合并相似的经验为更好的单条经验

    参数:
        similarity_threshold (float): 相似度阈值，超过此值的经验将被合并 (默认 0.7)
        domain_filter (str): 可选的领域过滤器，只整理特定领域的经验

    返回:
        str: 整理结果报告
    """
    print_message(f"🔄 开始整理经验库，相似度阈值: {similarity_threshold}")

    try:
        # 初始化模型
        model = Model()

        # 经验库文件路径
        experience_file = (
            "/Users/own/Workspace/MengLong/examples/app/terminal_try/experience.yaml"
        )

        # 检查经验库文件是否存在
        if not os.path.exists(experience_file):
            return "经验库文件不存在，无法进行整理。"

        # 读取经验库
        try:
            with open(experience_file, "r", encoding="utf-8") as f:
                experience_data = yaml.safe_load(f) or {}
        except Exception as e:
            print_message(f"读取经验库失败: {e}")
            return "无法读取经验库文件。"

        experiences = experience_data.get("experiences", [])
        if len(experiences) < 2:
            return "经验库中经验数量不足，无需整理。"

        original_count = len(experiences)
        print_message(f"原始经验数量: {original_count}")

        # 过滤领域（如果指定）
        if domain_filter:
            experiences = _filter_by_keywords(domain_filter, experiences)
            if len(experiences) < 2:
                return f"在 '{domain_filter}' 领域中找到的经验数量不足，无需整理。"
            print_message(f"领域过滤后经验数量: {len(experiences)}")

        # 找到相似的经验组
        similar_groups = _find_similar_experience_groups(
            experiences, similarity_threshold, model
        )

        if not similar_groups:
            return "未找到需要合并的相似经验。请尝试降低相似度阈值。"

        print_message(f"找到 {len(similar_groups)} 个相似经验组")

        # 合并每组相似经验
        merged_count = 0
        new_experiences = []
        processed_ids = set()

        for i, group in enumerate(similar_groups):
            if len(group) >= 2:  # 只处理有多个经验的组
                print_message(f"正在合并第 {i+1} 组经验...")
                merged_exp = _merge_similar_experiences(group, model)
                if merged_exp:
                    new_experiences.append(merged_exp)
                    processed_ids.update(
                        exp.get("id") for exp in group if exp.get("id")
                    )
                    merged_count += len(group)
                    titles = [exp.get("title", "Unknown") for exp in group]
                    print_message(f"✅ 合并了 {len(group)} 条相似经验: {titles}")
                else:
                    print_message(f"❌ 第 {i+1} 组经验合并失败")

        # 保留未被合并的经验
        if domain_filter:
            # 如果有领域过滤，需要重新读取完整的经验库
            with open(experience_file, "r", encoding="utf-8") as f:
                full_experience_data = yaml.safe_load(f) or {}
            all_experiences = full_experience_data.get("experiences", [])
            remaining_experiences = [
                exp for exp in all_experiences if exp.get("id") not in processed_ids
            ]
        else:
            remaining_experiences = [
                exp for exp in experiences if exp.get("id") not in processed_ids
            ]

        # 更新经验库
        final_experiences = remaining_experiences + new_experiences
        experience_data["experiences"] = final_experiences

        # 保存更新后的经验库
        with open(experience_file, "w", encoding="utf-8") as f:
            yaml.dump(
                experience_data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                indent=2,
            )

        # 生成统计报告
        final_count = len(final_experiences)
        reduced_count = original_count - final_count
        compression_ratio = (
            (reduced_count / original_count * 100) if original_count > 0 else 0
        )

        result = f"""
✅ 经验库整理完成

📊 整理统计:
  原始经验数: {original_count}
  相似经验组数: {len(similar_groups)}
  被合并的经验数: {merged_count}
  新生成的经验数: {len(new_experiences)}
  保留的经验数: {len(remaining_experiences)}
  最终经验数: {final_count}
  
📈 优化效果:
  减少经验数: {reduced_count}
  压缩比: {compression_ratio:.1f}%
  
💡 建议:
  {'经验库已得到有效整理，重复经验已合并。' if reduced_count > 0 else '当前相似度阈值下未找到可合并的经验，可尝试降低阈值。'}
"""

        return result

    except Exception as e:
        error_msg = f"经验库整理失败: {str(e)}"
        print_message(f"❌ {error_msg}", MessageType.ERROR)
        import traceback

        print_message(f"详细错误: {traceback.format_exc()}")
        return f"经验库整理遇到问题: {error_msg}"


@tool
def test_merge_workflow() -> str:
    """
    测试经验合并工作流程

    返回:
        str: 测试结果
    """
    print_message("🧪 开始测试经验合并工作流程...")

    try:
        # 1. 检查经验库
        debug_result = debug_experience_db()
        print_message("✅ 经验库检查完成")

        # 2. 测试embedding功能
        embed_result = test_embedding_functionality()
        print_message("✅ Embedding功能测试完成")

        # 3. 尝试合并（使用较低的阈值进行测试）
        merge_result = merge_similar_experiences(similarity_threshold=0.3)
        print_message("✅ 合并测试完成")

        return f"""
🧪 经验合并工作流程测试结果

📋 经验库状态:
{debug_result}

🔧 Embedding测试:
{embed_result}

🔄 合并测试:
{merge_result}
"""

    except Exception as e:
        return f"❌ 测试失败: {str(e)}"


if __name__ == "__main__":
    # 运行测试
    print(test_merge_workflow())
