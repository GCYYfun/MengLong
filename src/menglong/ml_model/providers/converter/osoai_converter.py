"""
OpenSource API 转换器实现。
"""

import traceback
from typing import Any, Dict, List, Optional

from menglong.ml_model.schema.ml_request import (
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ToolMessage,
)
from ...schema.ml_response import (
    ChatResponse,
    Content,
    ToolDesc,
    Usage,
    Message,
)
from .base_converter import BaseConverter, trace_converter_method
from ....utils.log import get_logger, print_json


class OpenSourceConverter(BaseConverter):
    """
    与 OpenSource API 兼容的消息转换器类。
    """

    @staticmethod
    @trace_converter_method
    def convert_request(messages):
        """将消息转换为OpenAI兼容格式。"""
        logger = get_logger("converter.opensource")

        # 验证输入
        messages = BaseConverter._validate_input_messages(
            messages, "OpenSource.convert_request"
        )

        format_messages = []

        try:
            for index, message in enumerate(messages):
                logger.debug(f"处理 OpenSource 消息 {index}: {type(message).__name__}")

                if isinstance(message, SystemMessage):
                    format_messages.append(
                        {"role": message.role, "content": message.content}
                    )
                elif isinstance(message, UserMessage):
                    format_messages.append(
                        {
                            "role": message.role,
                            "content": message.content,
                        }
                    )
                elif isinstance(message, AssistantMessage):
                    format_messages.append(
                        {"role": message.role, "content": message.content}
                    )
                elif isinstance(message, Message):
                    # 处理助手消息的列表内容
                    content = []
                    if message.tool_descriptions is not None:
                        logger.debug(
                            f"消息 {index} 包含 {len(message.tool_descriptions)} 个工具调用"
                        )
                        for tool_index, item in enumerate(message.tool_descriptions):
                            try:
                                tool_call = {
                                    "id": item.id,
                                    "type": item.type,
                                    "function": {
                                        "name": item.name,
                                        "arguments": item.arguments,
                                    },
                                }
                                content.append(tool_call)
                                logger.debug(f"工具调用 {tool_index}: {item.name}")
                            except Exception as e:
                                logger.error(f"处理工具调用 {tool_index} 时出错: {e}")

                                # 在终端输出完整的异常信息
                                print(f"\n❌ [OpenSource] 异常详情:")
                                print(f"   错误: {e}")
                                print("   完整堆栈信息:")
                                traceback.print_exc()
                                print("-" * 80)
                                raise ValueError(
                                    f"OpenSource 工具调用格式错误 (索引 {tool_index}): {e}"
                                )

                    format_messages.append(
                        {
                            "role": "assistant",
                            "content": message.content.text if message.content else "",
                            "tool_calls": content,
                        }
                    )
                elif isinstance(message, ToolMessage):
                    format_messages.append(
                        {
                            "role": message.role,
                            "tool_call_id": message.tool_id,
                            "content": message.content,
                        }
                    )
                else:
                    error_msg = f"不支持的消息类型 (索引 {index}): {type(message)}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

            logger.info(
                f"OpenSource 请求转换完成: {len(messages)} -> {len(format_messages)} 条消息"
            )
            return format_messages

        except Exception as e:
            logger.error(f"OpenSource 请求转换失败: {e}")

            # 在终端输出完整的异常信息
            print(f"\n❌ [OpenSource] 异常详情:")
            print(f"   错误: {e}")
            print("   完整堆栈信息:")
            traceback.print_exc()
            print("-" * 80)
            print_json(
                {
                    "error": str(e),
                    "input_message_count": len(messages),
                    "processed_count": len(format_messages),
                    "error_trace": traceback.format_exc(),
                },
                title="OpenSource 请求转换错误详情",
            )
            raise

    @staticmethod
    @trace_converter_method
    def normalize_response(response):
        """将OpenAI响应标准化为MLong的响应格式。"""
        logger = get_logger("converter.opensource")

        # 验证响应
        response = BaseConverter._validate_response(
            response, "OpenSource.normalize_response"
        )

        try:
            logger.debug(
                f"开始处理 OpenSource 响应，响应类型: {type(response).__name__}"
            )

            # 检查响应结构
            if not hasattr(response, "choices") or not response.choices:
                error_msg = "OpenSource 响应缺少 choices 字段或为空"
                logger.error(error_msg)
                raise ValueError(error_msg)

            response_choices = response.choices[0]
            logger.debug(
                f"处理第一个选择，消息类型: {type(response_choices.message).__name__}"
            )

            content = Content(text="")

            # 处理推理内容和文本内容
            if (
                hasattr(response_choices.message, "reasoning")
                and response_choices.message.reasoning is not None
            ):
                content.reasoning = response_choices.message.reasoning
                content.text = response_choices.message.content
                logger.debug("OpenSource 响应包含推理内容")
            else:
                content.text = response_choices.message.content
                logger.debug("OpenSource 响应仅包含文本内容")

            message = Message(
                content=content,
                finish_reason=(
                    response_choices.finish_reason
                    if hasattr(response_choices, "finish_reason")
                    else None
                ),
            )

            # 处理工具调用
            if (
                hasattr(response_choices.message, "tool_calls")
                and response_choices.message.tool_calls
            ):
                tool_calls_list = []
                logger.debug(
                    f"响应包含 {len(response_choices.message.tool_calls)} 个工具调用"
                )

                for tool_index, tool_call in enumerate(
                    response_choices.message.tool_calls
                ):
                    try:
                        tc = ToolDesc(
                            id=tool_call.id,
                            type=tool_call.type,
                            name=tool_call.function.name,
                            arguments=tool_call.function.arguments,
                        )
                        tool_calls_list.append(tc)
                        logger.debug(
                            f"工具调用 {tool_index}: {tool_call.function.name}"
                        )
                    except Exception as e:
                        logger.error(f"处理工具调用 {tool_index} 时出错: {e}")

                        # 在终端输出完整的异常信息
                        print(f"\n❌ [OpenSource] 异常详情:")
                        print(f"   错误: {e}")
                        print("   完整堆栈信息:")
                        traceback.print_exc()
                        print("-" * 80)
                        raise ValueError(
                            f"OpenSource 工具调用处理错误 (索引 {tool_index}): {e}"
                        )

                message.tool_descriptions = tool_calls_list

            # 处理使用情况
            if hasattr(response, "usage") and response.usage:
                usage = Usage(
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                )
                logger.debug(
                    f"Token 使用: 输入={usage.input_tokens}, 输出={usage.output_tokens}, 总计={usage.total_tokens}"
                )
            else:
                usage = Usage(input_tokens=0, output_tokens=0, total_tokens=0)
                logger.warning("响应中缺少使用情况信息")

            mlong_response = ChatResponse(
                message=message,
                model=getattr(response, "model", "unknown"),
                usage=usage,
            )

            logger.info("OpenSource 响应标准化完成")
            return mlong_response

        except Exception as e:
            logger.error(f"OpenSource 响应标准化失败: {e}")

            # 在终端输出完整的异常信息
            print(f"\n❌ [OpenSource] 异常详情:")
            print(f"   错误: {e}")
            print("   完整堆栈信息:")
            traceback.print_exc()
            print("-" * 80)
            print_json(
                {
                    "error": str(e),
                    "response_type": type(response).__name__,
                    "has_choices": hasattr(response, "choices"),
                    "choices_count": (
                        len(response.choices)
                        if hasattr(response, "choices") and response.choices
                        else 0
                    ),
                    "error_trace": traceback.format_exc(),
                },
                title="OpenSource 响应标准化错误详情",
            )
            raise

    @staticmethod
    @trace_converter_method
    def normalize_stream_response(response_stream):
        """
        将 OpenAI 流式响应转换为 MLong 的流式响应格式

        Args:
            response_stream: OpenAI 流式响应对象

        Returns:
            生成器，产生标准化的流式响应块
        """
        logger = get_logger("converter.opensource")
        logger.debug("开始处理 OpenSource 流式响应")

        chunk_count = 0

        try:
            for chunk in response_stream:
                chunk_count += 1
                logger.debug(f"处理 OpenSource 流式响应块 {chunk_count}")

                try:
                    if not chunk.choices:
                        logger.debug(f"跳过空选择的响应块 {chunk_count}")
                        continue

                    choice = chunk.choices[0]

                    # 处理文本内容
                    if hasattr(choice.delta, "content") and choice.delta.content:
                        yield {"type": "text", "content": choice.delta.content}
                        logger.debug(f"响应块 {chunk_count}: 文本内容")

                    # 处理思考过程内容
                    if hasattr(choice.delta, "reasoning") and choice.delta.reasoning:
                        yield {"type": "reasoning", "content": choice.delta.reasoning}
                        logger.debug(f"响应块 {chunk_count}: 推理内容")

                    # 处理工具调用
                    if hasattr(choice.delta, "tool_calls") and choice.delta.tool_calls:
                        for tool_call in choice.delta.tool_calls:
                            tool_call_data = {"type": "tool_call"}

                            # 初始工具调用信息（ID 和类型）
                            if hasattr(tool_call, "index"):
                                if hasattr(tool_call, "id"):
                                    tool_call_data["id"] = tool_call.id
                                if hasattr(tool_call, "type"):
                                    tool_call_data["tool_type"] = tool_call.type

                            # 函数信息
                            if hasattr(tool_call, "function"):
                                function_data = {}
                                if hasattr(tool_call.function, "name"):
                                    function_data["name"] = tool_call.function.name
                                if hasattr(tool_call.function, "arguments"):
                                    function_data["arguments"] = (
                                        tool_call.function.arguments
                                    )
                                if function_data:
                                    tool_call_data["function"] = function_data

                            yield tool_call_data
                            logger.debug(f"响应块 {chunk_count}: 工具调用")

                    # 处理完成原因
                    if choice.finish_reason:
                        yield {"type": "finish", "finish_reason": choice.finish_reason}
                        logger.debug(
                            f"响应块 {chunk_count}: 完成 ({choice.finish_reason})"
                        )

                except Exception as e:
                    logger.error(
                        f"处理 OpenSource 流式响应块 {chunk_count} 时出错: {e}"
                    )

                    # 在终端输出完整的异常信息
                    print(f"\n❌ [OpenSource] 异常详情:")
                    print(f"   错误: {e}")
                    print("   完整堆栈信息:")
                    traceback.print_exc()
                    print("-" * 80)
                    yield {"type": "error", "error": str(e), "chunk_index": chunk_count}
                    continue

            logger.info(f"OpenSource 流式响应处理完成，共处理 {chunk_count} 个响应块")

        except Exception as e:
            logger.error(f"OpenSource 流式响应处理失败: {e}")

            # 在终端输出完整的异常信息
            print(f"\n❌ [OpenSource] 异常详情:")
            print(f"   错误: {e}")
            print("   完整堆栈信息:")
            traceback.print_exc()
            print("-" * 80)
            print_json(
                {
                    "error": str(e),
                    "processed_chunks": chunk_count,
                    "error_trace": traceback.format_exc(),
                },
                title="OpenSource 流式响应处理错误详情",
            )
            raise
