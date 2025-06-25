from typing import List, Dict, Any, Optional, Union, Callable
from enum import Enum
import asyncio
import json
import time

from ..agent import Agent
from ...ml_model.schema.ml_request import UserMessage, ToolMessage
from ..component.context_manager import ContextManager
from ...utils.log import print_message, print_rule, MessageType

from ..component.tool_manager import ToolManager
from .workflow_manager import WorkflowManager


class SimpleChatAgent(Agent):
    """简化的聊天代理，专注于核心聊天功能"""

    def __init__(
        self,
        model_id: Optional[str] = None,
        system: Optional[str] = None,
        # tools: Any = ...,  # 使用 ... 作为默认值来区分 None 和未传递
    ):
        super().__init__(model_id=model_id)
        self.context = ContextManager()

        # 工具管理器
        self.tool_manager = ToolManager()

        # 工作流管理器
        # self.workflow_manager = WorkflowManager()

        # 自主任务执行相关属性
        self.autonomous_mode = False
        self.max_iterations = 10
        self.current_iteration = 0
        self.task_context = {}

        if system is not None:
            self.context.system = system

        # 自动注册工具
        # if tools is not ...:  # 如果明确传递了tools参数（包括None）
        #     self.tool_manager.auto_register_tools(tools)

    # ==================== 工具相关方法委托 ====================

    def register_tool(
        self, name: str, func, description: str = "", parameters: Dict = None
    ):
        """注册工具函数"""
        return self.tool_manager.register_tool(name, func, description, parameters)

    def register_tools_from_functions(self, *functions):
        """从函数列表中注册带有 @tool 装饰器的工具"""
        return self.tool_manager.register_tools_from_functions(*functions)

    def register_tools_from_module(self, module_or_namespace):
        """从模块或命名空间中自动注册所有用 @tool 装饰的函数"""
        return self.tool_manager.register_tools_from_module(module_or_namespace)

    def register_global_tools(self):
        """注册所有全局注册的工具"""
        return self.tool_manager.register_global_tools()

    def auto_register_tools(self, tools=None):
        """智能工具注册方法"""
        return self.tool_manager.auto_register_tools(tools)

    # ==================== 工作流相关方法委托 ====================

    def add_workflow_step(
        self, name: str, action: Callable, condition: Optional[Callable] = None
    ):
        """添加工作流步骤"""
        return self.workflow_manager.add_workflow_step(name, action, condition)

    async def add_workflow_step_async(
        self, name: str, action: Callable, condition: Optional[Callable] = None
    ):
        """异步添加工作流步骤"""
        return await self.workflow_manager.add_workflow_step_async(
            name, action, condition
        )

    def reset_workflow(self):
        """重置工作流状态"""
        return self.workflow_manager.reset_workflow()

    def get_workflow_status(self):
        """获取工作流状态"""
        return self.workflow_manager.get_workflow_status()

    # ==================== 核心聊天功能 ====================
    def chat(self, input_messages, **kwargs):
        """自动模式，支持工具调用"""
        self.context.add_user_message(input_messages)
        messages = self.context.messages

        if kwargs.get("tools") is not None:
            tools = kwargs.get("tools")
            self.tool_manager.add_tools(tools)
            # kwargs["tool_choice"] = self.tool_manager.format_tool_choice(
            #     self.model.provider
            # )

        # 如果有注册的工具，添加到请求中
        # if self.tool_manager.tools:
        #     kwargs["tools"] = self.tool_manager.format_tools_for_model(
        #         self.model.provider
        #     )
        #     kwargs["tool_choice"] = self.tool_manager.format_tool_choice(
        #         self.model.provider
        #     )

        try:
            res = self.model.chat(messages=messages, **kwargs)

            # 检查是否有工具调用
            if self._is_use_tool(res.message):
                # 添加助手的原始消息到上下文
                self.context._messages.context.append(res.message)

                # 执行工具调用并收集结果
                tool_results = self.tool_manager.execute_tool_call(
                    res.message.tool_descriptions
                )

                # 将工具结果添加到上下文
                for tool_result in tool_results:
                    tool_results_message = ToolMessage(
                        content=json.dumps(tool_result["content"], ensure_ascii=False),
                        tool_id=tool_result.get("id"),
                    )
                    self.context._messages.context.append(tool_results_message)

                # 重新获取消息列表
                messages = self.context.messages

                # 获取最终响应
                final_res = self.model.chat(
                    messages=messages,
                )
                r = final_res.message.content.text
            else:
                r = res.message.content.text

            # 处理推理内容
            if res.message.content.reasoning:
                self.context.add_assistant_reasoning(
                    query=input_messages,
                    reasoning=res.message.content.reasoning,
                    answers=r,
                )

            self.context.add_assistant_response(r)
            return r

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print_message(error_msg)
            return error_msg

    async def chat_async(self, input_messages, **kwargs):
        """异步 Chat"""
        self.context.add_user_message(input_messages)
        messages = self.context.messages

        # 如果有注册的工具，添加到请求中
        if kwargs.get("tools") is not None:
            tools = kwargs.get("tools")
            self.tool_manager.add_tools(tools)
            # kwargs["tool_choice"] = self.tool_manager.format_tool_choice(
            #     self.model.provider
            # )

        try:
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(
                None, lambda: self.model.chat(messages=messages, **kwargs)
            )

            # 检查是否有工具调用
            if self._is_use_tool(res.message):
                # 添加助手的原始消息到上下文
                self.context._messages.context.append(res.message)

                # 异步执行工具调用
                tool_results = await self.tool_manager.execute_tool_call_async(
                    res.message.tool_descriptions
                )

                # 将工具结果添加到上下文
                for tool_result in tool_results:
                    tool_results_message = ToolMessage(
                        content=json.dumps(tool_result["content"], ensure_ascii=False),
                        tool_id=tool_result.get("id"),
                    )
                    self.context._messages.context.append(tool_results_message)

                # 重新获取消息列表
                messages = self.context.messages

                # 获取最终响应
                final_res = await loop.run_in_executor(
                    None,
                    lambda: self.model.chat(
                        messages=messages, tools=kwargs.get("tools")
                    ),
                )
                r = final_res.message.content.text
            else:
                r = res.message.content.text

            # 处理推理内容
            if res.message.content.reasoning:
                self.context.add_assistant_reasoning(
                    query=input_messages,
                    reasoning=res.message.content.reasoning,
                    answers=r,
                )

            self.context.add_assistant_response(r)
            return r

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print_message(error_msg)
            return error_msg

    # def _normal_chat(self, input_messages, **kwargs):
    #     """普通聊天模式"""
    #     self.context.add_user_message(input_messages)
    #     messages = self.context.messages

    #     try:
    #         res = self.model.chat(messages=messages, **kwargs)
    #         r = res.message.content.text

    #         # 处理推理内容
    #         if res.message.content.reasoning:
    #             self.context.add_assistant_reasoning(
    #                 query=input_messages,
    #                 reasoning=res.message.content.reasoning,
    #                 answers=r,
    #             )
    #         self.context.add_assistant_response(r)
    #         return r

    #     except Exception as e:
    #         error_msg = f"Error: {str(e)}"
    #         self.context.add_assistant_response(error_msg)
    #         return error_msg

    # def _workflow_chat(self, input_messages, **kwargs):
    #     """工作流模式，支持多步骤任务"""
    #     self.context.add_user_message(input_messages)

    #     if not self.workflow_manager.workflow_steps:
    #         response = "No workflow steps defined. Please add workflow steps first."
    #         self.context.add_assistant_response(response)
    #         return response

    #     # 执行工作流
    #     try:
    #         final_result = self.workflow_manager.execute_workflow(
    #             input_messages, self.context
    #         )
    #         self.context.add_assistant_response(final_result)
    #         return final_result
    #     except Exception as e:
    #         error_msg = f"Workflow execution error: {str(e)}"
    #         self.context.add_assistant_response(error_msg)
    #         return error_msg

    # async def _async_workflow_chat(self, input_messages, **kwargs):
    #     """异步工作流聊天"""
    #     self.context.add_user_message(input_messages)

    #     if not self.workflow_manager.workflow_steps:
    #         response = "No workflow steps defined. Please add workflow steps first."
    #         self.context.add_assistant_response(response)
    #         return response

    #     try:
    #         final_result = await self.workflow_manager.execute_workflow_async(
    #             input_messages, self.context
    #         )
    #         self.context.add_assistant_response(final_result)
    #         return final_result
    #     except Exception as e:
    #         error_msg = f"Async workflow execution error: {str(e)}"
    #         self.context.add_assistant_response(error_msg)
    #         return error_msg

    def _is_use_tool(self, message):
        """检查消息是否包含工具调用"""
        if hasattr(message, "tool_descriptions") and message.tool_descriptions:
            return True
        return False

    # ==================== 自主任务执行功能 ====================

    def run(
        self,
        task: str = None,
        tools: Optional[List[Any]] = None,
        max_iterations: Optional[int] = 10,
    ) -> Dict[str, Any]:
        """运行代理（同步版本）"""
        if task:
            try:
                # 检查是否已在事件循环中
                try:
                    loop = asyncio.get_running_loop()
                    # 如果已在事件循环中，直接创建任务
                    task = asyncio.create_task(
                        self._autonomous_execute_task(task, tools, max_iterations)
                    )
                    return asyncio.get_event_loop().run_until_complete(task)
                except RuntimeError:
                    # 没有运行中的事件循环，使用 asyncio.run
                    return asyncio.run(
                        self._autonomous_execute_task(task, tools, max_iterations)
                    )
            except RuntimeError as e:
                if "cannot be called from a running event loop" in str(e):
                    raise RuntimeError(
                        "Cannot use run() from within an event loop. "
                        "Please use arun() instead for async environments."
                    ) from e
                raise
        return None

    async def run_async(
        self,
        task: str = None,
        tools: Optional[List[Any]] = None,
        max_iterations: Optional[int] = 10,
    ) -> Dict[str, Any]:
        """运行代理（异步版本）"""
        if task:
            result = await self._autonomous_execute_task(task, tools, max_iterations)
            return result
        return None

    async def _autonomous_execute_task(
        self,
        task_description: str,
        tools: Optional[List[Any]] = None,
        max_iterations: Optional[int] = 10,
    ) -> Dict[str, Any]:
        """自主执行任务的核心逻辑"""

        print_rule(f"开始自主执行任务", style="green")
        print_message(
            f" {task_description}", title="📋 任务描述:", msg_type=MessageType.INFO
        )

        # 设置自主任务模式
        self.autonomous_mode = True
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.task_context = {
            "original_task": task_description,
            "start_time": time.time(),
            "execution_log": [],
            "intermediate_results": [],
        }

        # 设置自主执行系统提示
        original_system = self.context.system
        autonomous_system = """你是一个自主任务执行助手。你的职责是：
1. 分析用户给出的任务
2. 制定执行计划
3. 逐步执行任务，使用可用的工具
4. 监控进度并调整策略
5. 确保任务完全完成

执行原则：
- 主动使用工具完成任务
- 遇到问题时寻找替代方案
- 定期检查任务完成情况
- 保持执行的连续性直到完成

请在每次响应中明确说明：
1. 当前正在执行的步骤
2. 使用的工具和原因
3. 下一步计划
4. 任务整体进度"""

        if original_system:
            self.context.system = f"{original_system}\n\n{autonomous_system}"
        else:
            self.context.system = autonomous_system

        try:
            # 初始化任务
            initial_prompt = f"""
我需要你自主完成以下任务：

任务描述：{task_description}

请分析这个任务，制定执行计划，然后开始执行。你有以下可用工具：
{self.tool_manager.get_available_tools_description()}

请开始执行，并在每步说明你的行动和理由。
"""

            last_response = ""
            task_completed = False

            while self.current_iteration < self.max_iterations and not task_completed:
                self.current_iteration += 1

                print_message(
                    f"{self.current_iteration}/{self.max_iterations}",
                    title="🔄 当前轮次:",
                    msg_type=MessageType.INFO,
                )

                # 构建当前轮次的提示
                if self.current_iteration == 1:
                    current_prompt = initial_prompt
                else:
                    current_prompt = f"""
继续执行任务。上次的执行结果：
{last_response}

请继续下一步执行，或者如果任务已完成，请进行最终验证。
当前已执行 {self.current_iteration-1} 轮，请确保任务的完整性。
"""

                # 让 Agent 执行下一步
                if tools is not None:  # 如果提供了工具列表
                    response = await self.chat_async(current_prompt, tools=tools)
                else:
                    response = await self.chat_async(current_prompt)

                last_response = response

                # 记录执行过程
                self.task_context["execution_log"].append(
                    {
                        "iteration": self.current_iteration,
                        "response": response,
                        "timestamp": time.time(),
                    }
                )

                print_message(
                    f"{response}", title="🤖 Agent 响应:", msg_type=MessageType.AGENT
                )

                # 检查是否提到任务完成
                completion_keywords = [
                    "任务完成",
                    "已完成",
                    "执行完毕",
                    "全部完成",
                    "任务结束",
                ]
                if any(keyword in response for keyword in completion_keywords):
                    print_message("🎯 检测到任务完成信号", MessageType.SUCCESS)

                    # 进行最终验证
                    final_validation = await self._perform_final_validation(
                        task_description
                    )
                    if final_validation["is_complete"]:
                        task_completed = True
                        print_message("✅ 任务执行完成！", MessageType.SUCCESS)
                    else:
                        print_message(
                            "⚠️ 任务尚未完全完成，继续执行", MessageType.WARNING
                        )

                # 短暂等待，避免过快执行
                await asyncio.sleep(1)

            # 生成执行报告
            execution_report = self._generate_execution_report(task_completed)

            if not task_completed:
                print_message("⏰ 达到最大执行轮次或任务未完成", MessageType.WARNING)

            return execution_report

        finally:
            # 恢复原始设置
            self.context.system = original_system
            self.autonomous_mode = False

    async def _perform_final_validation(self, task_description: str) -> Dict[str, Any]:
        """执行最终验证"""
        print_message("🔍 执行最终任务验证...", MessageType.INFO)

        # 从执行日志中提取已完成的项目
        completed_items = []
        for log_entry in self.task_context["execution_log"]:
            response = log_entry["response"]
            if "搜索" in response or "信息收集" in response:
                completed_items.append("信息收集")
            if "分析" in response or "数据分析" in response:
                completed_items.append("数据分析")
            if "报告" in response or "生成" in response:
                completed_items.append("报告生成")
            if "验证" in response or "检查" in response:
                completed_items.append("结果验证")

        # 使用验证提示
        validation_prompt = f"请验证以下任务是否完成：{task_description}。已完成的项目：{completed_items}"
        print_message(f"验证提示: {validation_prompt}", MessageType.INFO)
        if not self.tool_manager.curr_tools:
            validation_response = await self.chat_async(validation_prompt)
        else:
            validation_response = await self.chat_async(
                validation_prompt, tools=self.tool_manager.curr_tools
            )

        print_message(
            f"验证响应: {validation_response}",
            title="🔍 验证结果:",
            msg_type=MessageType.AGENT,
        )
        return {
            "is_complete": len(completed_items) >= 3,
            "completed_items": completed_items,
            "validation_response": validation_response,
        }

    def _generate_execution_report(self, task_completed: bool) -> Dict[str, Any]:
        """生成执行报告"""
        end_time = time.time()
        execution_time = end_time - self.task_context["start_time"]

        return {
            "task_description": self.task_context["original_task"],
            "status": "completed" if task_completed else "incomplete",
            "execution_time": execution_time,
            "iterations": self.current_iteration,
            "max_iterations": self.max_iterations,
            "execution_log": self.task_context["execution_log"],
            "success_rate": (
                1.0 if task_completed else self.current_iteration / self.max_iterations
            ),
        }

    # ==================== 实用方法 ====================

    def reset(self):
        """重置代理状态"""
        self.context.clear()
        self.workflow_manager.clear_workflow()

    async def clear_context_async(self):
        """异步清理上下文"""
        self.context.clear()
        await asyncio.sleep(0)

    async def get_context_summary_async(self) -> str:
        """异步获取上下文摘要"""
        if not self.context.messages:
            return "Empty context"

        message_count = len(self.context.messages)
        return f"Context contains {message_count} messages"

    # ==================== 批量处理方法 ====================

    async def batch_chat_async(self, message_list: List[str], **kwargs) -> List[str]:
        """异步批量处理多个消息"""
        tasks = []
        for message in message_list:
            task = self.chat_async(message, **kwargs)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(f"Error in message {i+1}: {str(result)}")
            else:
                processed_results.append(result)

        return processed_results

    async def sequential_chat_async(
        self, message_list: List[str], **kwargs
    ) -> List[str]:
        """异步顺序处理多个消息（保持上下文连续性）"""
        results = []
        for i, message in enumerate(message_list):
            try:
                result = await self.chat_async(message, **kwargs)
                results.append(result)
            except Exception as e:
                results.append(f"Error in message {i+1}: {str(e)}")
                break

        return results
