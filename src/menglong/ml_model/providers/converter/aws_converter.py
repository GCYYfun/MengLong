"""
AWS API 转换器实现。
"""

import traceback
from typing import Any, Generator, List, Dict, Tuple, Union
from ...schema.ml_request import (
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ToolMessage,
)
from ...schema.ml_response import (
    ChatResponse,
    Content,
    Usage,
    ToolDesc,
    Message,
    ContentDelta,
    StreamMessage,
    ChatStreamResponse,
)
from .base_converter import BaseConverter, trace_converter_method
from ....utils.log import get_logger, print_json

from ....utils.log import print_json


class AwsConverter(BaseConverter):
    """
    与 AWS API 兼容的消息转换器类。
    """

    reasoning = False
    tool = False

    @staticmethod
    @trace_converter_method
    def convert_request_messages(
        messages: List[Any],
    ) -> List[Any]:
        """
        将消息格式转换为 aws converse api 要求的格式

        Args:
            messages: 消息列表，每个消息为一个字典，包含角色和内容

        Returns:
            转换后的消息列表
        """
        logger = get_logger("converter.aws")

        # 验证输入
        messages = BaseConverter._validate_input_messages(
            messages, "AWS.convert_request_messages"
        )

        system_messages = []
        prompt_messages = []

        try:
            for index, message in enumerate(messages):
                logger.debug(f"处理 AWS 消息 {index}: {type(message).__name__}")

                if isinstance(message, SystemMessage):
                    system_messages.append({"text": message.content})
                elif isinstance(message, UserMessage):
                    prompt_messages.append(
                        {"role": message.role, "content": [{"text": message.content}]}
                    )
                elif isinstance(message, AssistantMessage):
                    prompt_messages.append(
                        {"role": message.role, "content": [{"text": message.content}]}
                    )
                elif isinstance(message, Message):
                    # 处理助手消息的列表内容
                    content = []
                    if message.content.text is not None:
                        content.append({"text": message.content.text})
                    if message.tool_descriptions is not None:
                        logger.debug(
                            f"消息 {index} 包含 {len(message.tool_descriptions)} 个工具调用"
                        )
                        for tool_index, item in enumerate(message.tool_descriptions):
                            try:
                                tool_use = {
                                    "toolUse": {
                                        "toolUseId": item.id,
                                        "name": item.name,
                                        "input": item.arguments,
                                    }
                                }
                                content.append(tool_use)
                                logger.debug(f"工具调用 {tool_index}: {item.name}")
                            except Exception as e:
                                logger.error(f"处理工具调用 {tool_index} 时出错: {e}")

                                # 在终端输出完整的异常信息
                                print(f"\n❌ [AWS] 异常详情:")
                                print(f"   错误: {e}")
                                print("   完整堆栈信息:")
                                traceback.print_exc()
                                print("-" * 80)
                                print(f"\n❌ [AWS] 工具调用处理异常:")
                                print(f"   工具索引: {tool_index}")
                                print(f"   错误: {e}")
                                traceback.print_exc()
                                print("-" * 40)
                                raise ValueError(
                                    f"AWS 工具调用格式错误 (索引 {tool_index}): {e}"
                                )
                    prompt_messages.append({"role": "assistant", "content": content})
                elif isinstance(message, ToolMessage):
                    # Handle ToolMessage for tool results
                    # 检查之前是否有工具调用结果消息被添加，如果没有则，添加一个工具结果
                    # 如果有，则将其追加到现有的工具结果中
                    if (
                        not prompt_messages
                        or "toolResult"
                        not in prompt_messages[-1].get("content", [{}])[0]
                    ):
                        prompt_messages.append(
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "toolResult": {
                                            "toolUseId": message.tool_id,
                                            "content": [{"text": message.content}],
                                        }
                                    }
                                ],
                            }
                        )
                    else:
                        prompt_messages[-1]["content"].append(
                            {
                                "toolResult": {
                                    "toolUseId": message.tool_id,
                                    "content": [{"text": message.content}],
                                }
                            }
                        )
                    logger.debug(f"工具结果消息 {index}: {message.tool_id}")
                elif isinstance(message, dict):
                    # 处理原始字典消息
                    if "role" in message and "content" in message:
                        role = message["role"]
                        content = message["content"]
                        if role == "system":
                            system_messages.append({"text": content})
                        else:
                            prompt_messages.append(
                                {"role": role, "content": [{"text": content}]}
                            )
                        logger.debug(f"字典消息 {index}: {role}")
                else:
                    error_msg = f"不支持的消息类型 (索引 {index}): {type(message)}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

            logger.info(
                f"AWS 请求转换完成: {len(messages)} -> 系统消息 {len(system_messages)}, 提示消息 {len(prompt_messages)}"
            )
            return system_messages, prompt_messages

        except Exception as e:
            logger.error(f"AWS 请求转换失败: {e}")

            # # 在终端输出完整的异常信息
            # print(f"\n❌ [AWS] 异常详情:")
            # print(f"   错误: {e}")
            # print("   完整堆栈信息:")
            # traceback.print_exc()
            # print("-" * 80)

            # 在终端输出完整的异常信息
            print(f"\n❌ [AWS] 请求转换异常:")
            print(f"   错误: {e}")
            print("   完整堆栈信息:")
            traceback.print_exc()
            print("-" * 80)

            print_json(
                {
                    "error": str(e),
                    "input_message_count": len(messages),
                    "system_messages_count": len(system_messages),
                    "prompt_messages_count": len(prompt_messages),
                    "error_trace": traceback.format_exc(),
                },
                title="AWS 请求转换错误详情",
            )
            raise

    @staticmethod
    @trace_converter_method
    def normalize_response(response, debug=False) -> ChatResponse:
        """将AWS响应标准化为MLong的响应格式。"""
        logger = get_logger("converter.aws")

        # 验证响应
        response = BaseConverter._validate_response(response, "AWS.normalize_response")

        try:
            if debug:
                print_json(response, title="AWS 响应详情")

            logger.debug(f"开始处理 AWS 响应，响应类型: {type(response).__name__}")

            # 检查响应结构
            if "output" not in response:
                error_msg = "AWS 响应缺少 output 字段"
                logger.error(error_msg)
                raise ValueError(error_msg)

            output = response.get("output")
            if not output or "message" not in output:
                error_msg = "AWS 响应的 output 缺少 message 字段"
                logger.error(error_msg)
                raise ValueError(error_msg)

            content = Content(text=None)

            try:
                if AwsConverter.reasoning:  # 纯推理
                    logger.debug("处理推理响应")
                    content.reasoning = output["message"]["content"][0][
                        "reasoningContent"
                    ]["reasoningText"]["text"]
                    content.text = output["message"]["content"][1]["text"]
                    message = Message(
                        content=content,
                        finish_reason=response["stopReason"],
                    )
                elif response["stopReason"] == "tool_use":
                    logger.debug("处理工具使用响应")
                    index = 0
                    if "text" in output["message"]["content"][index]:
                        content.text = output["message"]["content"][index]["text"]
                        index += 1

                    # 处理工具调用
                    tool_items = output["message"]["content"][index:]
                    logger.debug(f"响应包含 {len(tool_items)} 个工具调用")

                    descriptions = []
                    for tool_index, item in enumerate(tool_items):
                        try:
                            tool_desc = ToolDesc(
                                id=item["toolUse"]["toolUseId"],
                                type="tool_use",
                                name=item["toolUse"]["name"],
                                arguments=item["toolUse"]["input"],
                            )
                            descriptions.append(tool_desc)
                            logger.debug(f"工具调用 {tool_index}: {tool_desc.name}")
                        except Exception as e:
                            logger.error(f"处理工具调用 {tool_index} 时出错: {e}")

                            # # 在终端输出完整的异常信息
                            # print(f"\n❌ [AWS] 异常详情:")
                            # print(f"   错误: {e}")
                            # print("   完整堆栈信息:")
                            # traceback.print_exc()
                            # print("-" * 80)
                            print(f"\n❌ [AWS] 响应工具调用处理异常:")
                            print(f"   工具索引: {tool_index}")
                            print(f"   错误: {e}")
                            traceback.print_exc()
                            print("-" * 40)
                            raise ValueError(
                                f"AWS 工具调用处理错误 (索引 {tool_index}): {e}"
                            )

                    message = Message(
                        content=content,
                        finish_reason=response["stopReason"],
                        tool_descriptions=descriptions,
                    )
                else:
                    logger.debug("处理普通文本响应")
                    if not output["message"]["content"]:
                        logger.warning("响应内容为空")
                        content.text = ""
                    else:
                        content.text = output["message"]["content"][0]["text"]
                    message = Message(
                        content=content,
                        finish_reason=response["stopReason"],
                    )
            except (KeyError, IndexError, TypeError) as e:
                logger.error(f"解析 AWS 响应内容时出错: {e}")
                raise ValueError(f"AWS 响应格式错误: {e}")

            # 处理使用情况
            usage_data = response.get("usage", {})
            usage = Usage(
                input_tokens=usage_data.get("inputTokens", 0),
                output_tokens=usage_data.get("outputTokens", 0),
                total_tokens=usage_data.get("totalTokens", 0),
            )

            if usage.total_tokens > 0:
                logger.debug(
                    f"Token 使用: 输入={usage.input_tokens}, 输出={usage.output_tokens}, 总计={usage.total_tokens}"
                )
            else:
                logger.warning("响应中缺少使用情况信息")

            mlong_response = ChatResponse(
                message=message, model=response.get("modelId", "unknown"), usage=usage
            )

            logger.info("AWS 响应标准化完成")
            return mlong_response

        except Exception as e:
            logger.error(f"AWS 响应标准化失败: {e}")

            # # 在终端输出完整的异常信息
            # print(f"\n❌ [AWS] 异常详情:")
            # print(f"   错误: {e}")
            # print("   完整堆栈信息:")
            # traceback.print_exc()
            # print("-" * 80)

            # 在终端输出完整的异常信息
            print(f"\n❌ [AWS] 响应标准化异常:")
            print(f"   错误: {e}")
            print("   完整堆栈信息:")
            traceback.print_exc()
            print("-" * 80)

            print_json(
                {
                    "error": str(e),
                    "response_keys": (
                        list(response.keys())
                        if isinstance(response, dict)
                        else "non-dict"
                    ),
                    "has_output": (
                        "output" in response if isinstance(response, dict) else False
                    ),
                    "stop_reason": (
                        response.get("stopReason")
                        if isinstance(response, dict)
                        else "unknown"
                    ),
                    "error_trace": traceback.format_exc(),
                },
                title="AWS 响应标准化错误详情",
            )
            raise

    @staticmethod
    @trace_converter_method
    def normalize_stream_response(
        response_stream,
        debug: bool = False,
    ) -> Generator:
        """将AWS流式响应标准化为MLong的响应格式。"""
        logger = get_logger("converter.aws")
        logger.debug("开始处理 AWS 流式响应")

        chunk_count = 0

        try:
            # 返回生成器
            for chunk in response_stream.get("stream", []):
                chunk_count += 1
                logger.debug(f"处理 AWS 流式响应块 {chunk_count}")

                try:
                    # 处理流式响应
                    delta = ContentDelta()
                    start = None
                    finish = None
                    usage = None

                    if debug:
                        print_json(chunk, title=f"AWS 响应块 {chunk_count}")

                    # 处理不同类型的消息
                    match chunk:
                        case {"contentBlockDelta": block}:
                            # 处理文本内容
                            if block.get("delta").get("text") is not None:
                                delta.text = block.get("delta").get("text")
                                logger.debug(f"响应块 {chunk_count}: 文本内容")
                            # 处理推理内容
                            if block.get("delta").get("reasoningContent") is not None:
                                delta.reasoning = (
                                    block.get("delta")
                                    .get("reasoningContent")
                                    .get("text")
                                )
                                logger.debug(f"响应块 {chunk_count}: 推理内容")
                        case {"messageStart": message_start}:
                            # 处理推理内容
                            start = message_start.get("role")
                            logger.debug(f"响应块 {chunk_count}: 消息开始 ({start})")
                        case {"contentBlockStop": content_stop}:
                            # 处理内容块停止
                            content_stop_index = content_stop.get("contentBlockIndex")
                            finish = f"{content_stop_index}"
                            logger.debug(f"响应块 {chunk_count}: 内容块停止 ({finish})")
                        case {"messageStop": message_stop}:
                            if message_stop.get("stopReason") == "end_turn":
                                finish = "end_turn"
                                logger.debug(f"响应块 {chunk_count}: 消息停止")
                        case {"metadata": metadata}:
                            # 处理元数据
                            usage_data = metadata.get("usage", {})
                            usage = Usage(
                                input_tokens=usage_data.get("inputTokens", 0),
                                output_tokens=usage_data.get("outputTokens", 0),
                                total_tokens=usage_data.get("totalTokens", 0),
                            )
                            logger.debug(
                                f"响应块 {chunk_count}: 元数据 (Token 使用: {usage.total_tokens})"
                            )
                        case _:
                            logger.debug(f"响应块 {chunk_count}: 未知类型")

                    message = StreamMessage(
                        delta=delta,
                        start_reason=start,
                        finish_reason=finish,
                    )
                    yield ChatStreamResponse(
                        message=message, model_id=None, usage=usage
                    )

                except Exception as e:
                    logger.error(f"处理 AWS 流式响应块 {chunk_count} 时出错: {e}")

                    # # 在终端输出完整的异常信息
                    # print(f"\n❌ [AWS] 异常详情:")
                    # print(f"   错误: {e}")
                    # print("   完整堆栈信息:")
                    # traceback.print_exc()
                    # print("-" * 80)
                    print(f"\n❌ [AWS] 流式响应块处理异常:")
                    print(f"   响应块索引: {chunk_count}")
                    print(f"   错误: {e}")
                    traceback.print_exc()
                    print("-" * 40)
                    # 生成错误响应
                    error_delta = ContentDelta(text=f"错误: {str(e)}")
                    error_message = StreamMessage(
                        delta=error_delta, finish_reason="error"
                    )
                    yield ChatStreamResponse(
                        message=error_message, model_id=None, usage=None
                    )
                    continue

            logger.info(f"AWS 流式响应处理完成，共处理 {chunk_count} 个响应块")

        except Exception as e:
            logger.error(f"AWS 流式响应处理失败: {e}")

            # # 在终端输出完整的异常信息
            # print(f"\n❌ [AWS] 异常详情:")
            # print(f"   错误: {e}")
            # print("   完整堆栈信息:")
            # traceback.print_exc()
            # print("-" * 80)

            # 在终端输出完整的异常信息
            print(f"\n❌ [AWS] 流式响应处理异常:")
            print(f"   错误: {e}")
            print("   完整堆栈信息:")
            traceback.print_exc()
            print("-" * 80)

            print_json(
                {
                    "error": str(e),
                    "processed_chunks": chunk_count,
                    "debug": debug,
                    "error_trace": traceback.format_exc(),
                },
                title="AWS 流式响应处理错误详情",
            )
            raise

    @staticmethod
    @trace_converter_method
    def convert_tools(tools: List, model_id: str) -> List[Dict]:
        """将工具转换为适合模型的格式。"""
        logger = get_logger("converter.aws")

        if not tools:
            logger.debug("没有工具需要转换")
            return []

        try:
            formatted_tools = []
            logger.debug(f"开始转换 {len(tools)} 个工具，模型: {model_id}")

            for tool_index, tool in enumerate(tools):
                try:
                    tool_info = tool._tool_info
                    match model_id:
                        case model_id if "claude" in model_id:
                            formatted_tool = {
                                "toolSpec": {
                                    "name": tool_info.name,
                                    "description": tool_info.description,
                                    "inputSchema": {"json": tool_info.parameters},
                                }
                            }
                        case _:
                            formatted_tool = {
                                "toolSpec": {
                                    "name": tool_info.name,
                                    "description": tool_info.description,
                                    "inputSchema": {"json": tool_info.parameters},
                                }
                            }
                    formatted_tools.append(formatted_tool)
                    logger.debug(f"工具转换 {tool_index}: {tool_info.name}")
                except Exception as e:
                    logger.error(f"转换工具 {tool_index} 时出错: {e}")

                    # # 在终端输出完整的异常信息
                    # print(f"\n❌ [AWS] 异常详情:")
                    # print(f"   错误: {e}")
                    # print("   完整堆栈信息:")
                    # traceback.print_exc()
                    # print("-" * 80)
                    print(f"\n❌ [AWS] 工具转换异常:")
                    print(f"   工具索引: {tool_index}")
                    print(f"   错误: {e}")
                    traceback.print_exc()
                    print("-" * 40)
                    raise ValueError(f"AWS 工具转换错误 (索引 {tool_index}): {e}")

            logger.info(f"AWS 工具转换完成: {len(tools)} -> {len(formatted_tools)}")
            return formatted_tools

        except Exception as e:
            logger.error(f"AWS 工具转换失败: {e}")

            # # 在终端输出完整的异常信息
            # print(f"\n❌ [AWS] 异常详情:")
            # print(f"   错误: {e}")
            # print("   完整堆栈信息:")
            # traceback.print_exc()
            # print("-" * 80)

            # 在终端输出完整的异常信息
            print(f"\n❌ [AWS] 工具转换异常:")
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
                title="AWS 工具转换错误详情",
            )
            raise
