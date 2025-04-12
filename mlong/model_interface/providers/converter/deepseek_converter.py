"""
Deepseek API 转换器实现。
"""

from mlong.model_interface.schema.response import (
    ChatResponse,
    Content,
    Function,
    ToolCall,
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
        """将MLong消息转换为Deepseek兼容格式。"""
        pass

    @staticmethod
    def normalize_response(response):
        """将Deepseek响应标准化为MLong的响应格式。"""
        content = Content(text_content="")
        response_choices = response.choices[0]

        if DeepseekConverter.reasoning:
            content.reasoning_content = response_choices.message.reasoning_content
            content.text_content = response_choices.message.content
        else:
            content.text_content = response_choices.message.content

        message = Message(content=content, finish_reason=response_choices.finish_reason)

        # 处理工具调用
        if (
            hasattr(response_choices.message, "tool_calls")
            and response_choices.message.tool_calls
        ):
            tool_calls_list = []
            for tool_call in response_choices.message.tool_calls:
                tc = ToolCall(
                    id=tool_call.id,
                    type=tool_call.type,
                    function=Function(
                        name=tool_call.function.name,
                        arguments=tool_call.function.arguments,
                    ),
                )
                tool_calls_list.append(tc)
            message.tool_calls = tool_calls_list
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
