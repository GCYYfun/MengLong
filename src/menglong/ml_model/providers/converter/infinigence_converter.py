"""
Infinigence API 转换器实现。
"""

import traceback
from typing import Dict, List
from ...schema.ml_request import (
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
    ContentDelta,
    StreamMessage,
    ChatStreamResponse,
)
from .base_converter import BaseConverter, trace_converter_method
from ....utils.log import get_logger, print_json


class InfinigenceConverter(BaseConverter):
    """
    与 Infinigence API 兼容的消息转换器类。
    """

    reasoning = False

    @staticmethod
    @trace_converter_method
    def convert_request(messages, debug=True):
        """将消息转换为OpenAI兼容格式。"""
        logger = get_logger("converter.infinigence")

        # 验证输入
        messages = BaseConverter._validate_input_messages(
            messages, "Infinigence.convert_request"
        )

        format_messages = []

        try:
            for index, message in enumerate(messages):
                logger.debug(f"处理 Infinigence 消息 {index}: {type(message).__name__}")

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
                                print(f"\n❌ [Infinigence] 异常详情:")
                                print(f"   错误: {e}")
                                print("   完整堆栈信息:")
                                traceback.print_exc()
                                print("-" * 80)
                                raise ValueError(
                                    f"Infinigence 工具调用格式错误 (索引 {tool_index}): {e}"
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
                    logger.debug(f"工具消息 {index}: {message.tool_id}")
                else:
                    error_msg = f"不支持的消息类型 (索引 {index}): {type(message)}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

            logger.info(
                f"Infinigence 请求转换完成: {len(messages)} -> {len(format_messages)} 条消息"
            )
            return format_messages

        except Exception as e:
            logger.error(f"Infinigence 请求转换失败: {e}")

            # 在终端输出完整的异常信息
            print(f"\n❌ [Infinigence] 异常详情:")
            print(f"   错误: {e}")
            print("   完整堆栈信息:")
            traceback.print_exc()
            print("-" * 80)
            print_json(
                {
                    "error": str(e),
                    "input_message_count": len(messages),
                    "processed_count": len(format_messages),
                    "debug": debug,
                    "error_trace": traceback.format_exc(),
                },
                title="Infinigence 请求转换错误详情",
            )
            raise

    @staticmethod
    @trace_converter_method
    def normalize_response(response, debug=False):
        """将Infinigence响应标准化为MLong的响应格式。"""
        logger = get_logger("converter.infinigence")

        # 验证响应
        response = BaseConverter._validate_response(
            response, "Infinigence.normalize_response"
        )

        try:
            if debug:
                print_json(response, title="Infinigence 响应详情")

            logger.debug(
                f"开始处理 Infinigence 响应，响应类型: {type(response).__name__}"
            )

            # 检查响应结构（字典格式）
            if not isinstance(response, dict):
                error_msg = (
                    f"Infinigence 响应应为字典格式，当前类型: {type(response).__name__}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            if "choices" not in response or not response["choices"]:
                error_msg = "Infinigence 响应缺少 choices 字段或为空"
                logger.error(error_msg)
                raise ValueError(error_msg)

            response_choices = response["choices"][0]
            logger.debug(f"处理第一个选择")

            content = Content(text="")

            if InfinigenceConverter.reasoning:
                content.reasoning = response_choices["message"]["reasoning_content"]
                content.text = response_choices["message"]["content"]
                logger.debug("Infinigence 响应包含推理内容")
            else:
                content.text = response_choices["message"]["content"]
                logger.debug("Infinigence 响应仅包含文本内容")

            message = Message(
                content=content, finish_reason=response_choices["finish_reason"]
            )

            # 处理工具调用
            if (
                "tool_calls" in response_choices["message"]
                and response_choices["message"]["tool_calls"]
            ):
                tool_calls_list = []
                tool_calls = response_choices["message"]["tool_calls"]
                logger.debug(f"响应包含 {len(tool_calls)} 个工具调用")

                for tool_index, tool_call in enumerate(tool_calls):
                    try:
                        tc = ToolDesc(
                            id=tool_call["id"],
                            type=tool_call["type"],
                            name=tool_call["function"]["name"],
                            arguments=tool_call["function"]["arguments"],
                        )
                        tool_calls_list.append(tc)
                        logger.debug(
                            f"工具调用 {tool_index}: {tool_call['function']['name']}"
                        )
                    except Exception as e:
                        logger.error(f"处理工具调用 {tool_index} 时出错: {e}")

                        # 在终端输出完整的异常信息
                        print(f"\n❌ [Infinigence] 异常详情:")
                        print(f"   错误: {e}")
                        print("   完整堆栈信息:")
                        traceback.print_exc()
                        print("-" * 80)
                        raise ValueError(
                            f"Infinigence 工具调用处理错误 (索引 {tool_index}): {e}"
                        )

                message.tool_descriptions = tool_calls_list

            # 处理使用情况
            if "usage" in response and response["usage"]:
                usage = Usage(
                    input_tokens=response["usage"]["prompt_tokens"],
                    output_tokens=response["usage"]["completion_tokens"],
                    total_tokens=response["usage"]["total_tokens"],
                )
                logger.debug(
                    f"Token 使用: 输入={usage.input_tokens}, 输出={usage.output_tokens}, 总计={usage.total_tokens}"
                )
            else:
                usage = Usage(input_tokens=0, output_tokens=0, total_tokens=0)
                logger.warning("响应中缺少使用情况信息")

            mlong_response = ChatResponse(
                message=message, model=response.get("model", "unknown"), usage=usage
            )

            logger.info("Infinigence 响应标准化完成")
            return mlong_response

        except Exception as e:
            logger.error(f"Infinigence 响应标准化失败: {e}")

            # 在终端输出完整的异常信息
            print(f"\n❌ [Infinigence] 异常详情:")
            print(f"   错误: {e}")
            print("   完整堆栈信息:")
            traceback.print_exc()
            print("-" * 80)
            print_json(
                {
                    "error": str(e),
                    "response_type": type(response).__name__,
                    "response_keys": (
                        list(response.keys())
                        if isinstance(response, dict)
                        else "non-dict"
                    ),
                    "has_choices": (
                        "choices" in response if isinstance(response, dict) else False
                    ),
                    "debug": debug,
                    "error_trace": traceback.format_exc(),
                },
                title="Infinigence 响应标准化错误详情",
            )
            raise

    @staticmethod
    @trace_converter_method
    def normalize_stream_response(response_stream):
        """将Infinigence流式响应标准化为MLong的流式响应格式。"""
        logger = get_logger("converter.infinigence")
        logger.debug("开始处理 Infinigence 流式响应")

        chunk_count = 0

        try:
            for chunk in response_stream:
                chunk_count += 1
                logger.debug(f"处理 Infinigence 流式响应块 {chunk_count}")

                try:
                    if not chunk["choices"]:
                        logger.debug(f"跳过空选择的响应块 {chunk_count}")
                        continue

                    choice = chunk["choices"][0]

                    # 处理文本和思考内容
                    if InfinigenceConverter.reasoning:
                        delta = ContentDelta(
                            text_content=(
                                choice["delta"]["content"]
                                if "content" in choice["delta"]
                                else None
                            ),
                            reasoning_content=(
                                choice["delta"]["reasoning_content"]
                                if "reasoning_content" in choice["delta"]
                                else None
                            ),
                        )
                        logger.debug(f"响应块 {chunk_count}: 推理模式")
                    else:
                        delta = ContentDelta(
                            text_content=(
                                choice["delta"]["content"]
                                if "content" in choice["delta"]
                                else None
                            ),
                            reasoning_content=None,
                        )
                        logger.debug(f"响应块 {chunk_count}: 普通模式")

                    message = StreamMessage(
                        delta=delta, finish_reason=choice["finish_reason"]
                    )

                    # 处理工具调用
                    if (
                        "tool_calls" in choice["delta"]
                        and choice["delta"]["tool_calls"]
                    ):
                        tool_calls_list = []
                        for tool_call in choice["delta"]["tool_calls"]:
                            tool_call_dict = {
                                "id": tool_call["id"] if "id" in tool_call else None,
                                "type": (
                                    tool_call["type"] if "type" in tool_call else None
                                ),
                                "function": {
                                    "name": (
                                        tool_call["function"]["name"]
                                        if "name" in tool_call["function"]
                                        else None
                                    ),
                                    "arguments": (
                                        tool_call["function"]["arguments"]
                                        if "arguments" in tool_call["function"]
                                        else None
                                    ),
                                },
                            }
                            tool_calls_list.append(tool_call_dict)
                        # 将工具调用信息添加到响应中
                        stream_response = ChatStreamResponse(
                            message=message, tool_calls=tool_calls_list
                        )
                        logger.debug(f"响应块 {chunk_count}: 工具调用")
                    else:
                        stream_response = ChatStreamResponse(message=message)

                    yield stream_response

                except Exception as e:
                    logger.error(
                        f"处理 Infinigence 流式响应块 {chunk_count} 时出错: {e}"
                    )

                    # 在终端输出完整的异常信息
                    print(f"\n❌ [Infinigence] 异常详情:")
                    print(f"   错误: {e}")
                    print("   完整堆栈信息:")
                    traceback.print_exc()
                    print("-" * 80)
                    # 生成错误响应
                    error_message = StreamMessage(
                        delta=ContentDelta(text_content=f"错误: {str(e)}"),
                        finish_reason="error",
                    )
                    yield ChatStreamResponse(message=error_message)
                    continue

            logger.info(f"Infinigence 流式响应处理完成，共处理 {chunk_count} 个响应块")

        except Exception as e:
            logger.error(f"Infinigence 流式响应处理失败: {e}")

            # 在终端输出完整的异常信息
            print(f"\n❌ [Infinigence] 异常详情:")
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
                title="Infinigence 流式响应处理错误详情",
            )
            raise

    @staticmethod
    @trace_converter_method
    def convert_tools(tools: List, model_id: str = None) -> List[Dict]:
        """将工具转换为适合模型的格式。"""
        logger = get_logger("converter.infinigence")

        if not tools:
            logger.debug("没有工具需要转换")
            return []

        try:
            formatted_tools = []
            logger.debug(f"开始转换 {len(tools)} 个工具")

            for tool_index, tool in enumerate(tools):
                try:
                    tool_info = tool._tool_info
                    formatted_tool = {
                        "type": "function",
                        "function": {
                            "name": tool_info.name,
                            "description": tool_info.description,
                            "parameters": tool_info.parameters,
                        },
                    }
                    formatted_tools.append(formatted_tool)
                    logger.debug(f"工具转换 {tool_index}: {tool_info.name}")
                except Exception as e:
                    logger.error(f"转换工具 {tool_index} 时出错: {e}")

                    # 在终端输出完整的异常信息
                    print(f"\n❌ [Infinigence] 异常详情:")
                    print(f"   错误: {e}")
                    print("   完整堆栈信息:")
                    traceback.print_exc()
                    print("-" * 80)
                    raise ValueError(
                        f"Infinigence 工具转换错误 (索引 {tool_index}): {e}"
                    )

            logger.info(
                f"Infinigence 工具转换完成: {len(tools)} -> {len(formatted_tools)}"
            )
            return formatted_tools

        except Exception as e:
            logger.error(f"Infinigence 工具转换失败: {e}")

            # 在终端输出完整的异常信息
            print(f"\n❌ [Infinigence] 异常详情:")
            print(f"   错误: {e}")
            print("   完整堆栈信息:")
            traceback.print_exc()
            print("-" * 80)
            print_json(
                {
                    "error": str(e),
                    "tools_count": len(tools) if tools else 0,
                    "model_id": model_id,
                    "error_trace": traceback.format_exc(),
                },
                title="Infinigence 工具转换错误详情",
            )
            raise
