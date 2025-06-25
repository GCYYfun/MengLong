"""
Deepseek API 转换器实现。
"""

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
from .base_converter import BaseConverter


class DeepseekConverter(BaseConverter):
    """
    与 Deepseek API 兼容的消息转换器类。
    """

    reasoning = False

    @staticmethod
    def convert_request(messages):
        """将消息转换为OpenAI兼容格式。"""
        format_messages = []
        for message in messages:
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
                    for item in message.tool_descriptions:
                        content.append(
                            {
                                "id": item.id,
                                "type": item.type,
                                "function": {
                                    "name": item.name,
                                    "arguments": item.arguments,
                                },
                            }
                        )
                format_messages.append(
                    {
                        "role": "assistant",
                        "content": message.content.text,
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
                raise ValueError(f"Unsupported message type: {type(message)}")
        return format_messages

    @staticmethod
    def normalize_response(response):
        """将Deepseek响应标准化为MLong的响应格式。"""
        content = Content(text="")
        response_choices = response.choices[0]

        if DeepseekConverter.reasoning:
            content.reasoning = response_choices.message.reasoning_content
            content.text = response_choices.message.content
        else:
            content.text = response_choices.message.content

        message = Message(content=content, finish_reason=response_choices.finish_reason)

        # 处理工具调用
        if (
            hasattr(response_choices.message, "tool_calls")
            and response_choices.message.tool_calls
        ):
            tool_calls_list = []
            for tool_call in response_choices.message.tool_calls:
                tc = ToolDesc(
                    id=tool_call.id,
                    type=tool_call.type,
                    name=tool_call.function.name,
                    arguments=tool_call.function.arguments,
                )
                tool_calls_list.append(tc)
            message.tool_descriptions = tool_calls_list
        usage = Usage(
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )

        mlong_response = ChatResponse(
            message=message, model=response.model, usage=usage
        )
        return mlong_response

    @staticmethod
    def normalize_stream_response(response_stream):
        """将Deepseek流式响应标准化为MLong的流式响应格式。"""
        # 返回生成器
        for chunk in response_stream:
            if not chunk.choices:
                continue

            choice = chunk.choices[0]

            # 处理文本和思考内容
            if DeepseekConverter.reasoning:
                delta = ContentDelta(
                    text_content=(
                        choice.delta.content
                        if hasattr(choice.delta, "content")
                        else None
                    ),
                    reasoning_content=(
                        choice.delta.reasoning_content
                        if hasattr(choice.delta, "reasoning_content")
                        else None
                    ),
                )
            else:
                delta = ContentDelta(
                    text_content=(
                        choice.delta.content
                        if hasattr(choice.delta, "content")
                        else None
                    ),
                    reasoning_content=None,
                )

            message = StreamMessage(delta=delta, finish_reason=choice.finish_reason)

            # 处理工具调用
            if hasattr(choice.delta, "tool_calls") and choice.delta.tool_calls:
                tool_calls_list = []
                for tool_call in choice.delta.tool_calls:
                    tool_call_dict = {
                        "id": tool_call.id if hasattr(tool_call, "id") else None,
                        "type": tool_call.type if hasattr(tool_call, "type") else None,
                        "function": {
                            "name": (
                                tool_call.function.name
                                if hasattr(tool_call.function, "name")
                                else None
                            ),
                            "arguments": (
                                tool_call.function.arguments
                                if hasattr(tool_call.function, "arguments")
                                else None
                            ),
                        },
                    }
                    tool_calls_list.append(tool_call_dict)
                # 将工具调用信息添加到响应中
                stream_response = ChatStreamResponse(
                    message=message, tool_calls=tool_calls_list
                )
            else:
                stream_response = ChatStreamResponse(message=message)

            yield stream_response

    @staticmethod
    def convert_tools(tools: List, model_id: str) -> List[Dict]:
        """将工具转换为适合模型的格式。"""
        if not tools:
            return []

        formatted_tools = []
        for tool in tools:
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

        return formatted_tools
