"""
OpenAI API 转换器实现。
"""

from mlong.model_interface.schema.response import (
    ChatResponse,
    Content,
    Function,
    ToolCall,
    Usage,
    Message,
)
from .base_converter import BaseConverter


class OpenAIConverter(BaseConverter):
    """
    与 OpenAI API 兼容的消息转换器类。
    """

    @staticmethod
    def convert_request(messages):
        """将消息转换为OpenAI兼容格式。"""
        pass

    @staticmethod
    def normalize_response(response):
        """将OpenAI响应标准化为MLong的响应格式。"""

        content = Content(text_content="")
        response_choices = response.choices[0]
        if (
            hasattr(response_choices.message, "reasoning")
            and response_choices.message.reasoning is not None
        ):
            content.reasoning_content = response_choices.message.reasoning
            content.text_content = response_choices.message.content
        else:
            content.text_content = response_choices.message.content

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
        """
        将 OpenAI 流式响应转换为 MLong 的流式响应格式

        Args:
            response_stream: OpenAI 流式响应对象

        Returns:
            生成器，产生标准化的流式响应块
        """
        for chunk in response_stream:
            if not chunk.choices:
                continue

            choice = chunk.choices[0]

            # 处理文本内容
            if hasattr(choice.delta, "content") and choice.delta.content:
                yield {"type": "text", "content": choice.delta.content}

            # 处理思考过程内容
            if hasattr(choice.delta, "reasoning") and choice.delta.reasoning:
                yield {"type": "reasoning", "content": choice.delta.reasoning}

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
                            function_data["arguments"] = tool_call.function.arguments
                        if function_data:
                            tool_call_data["function"] = function_data

                    yield tool_call_data

            # 处理完成原因
            if choice.finish_reason:
                yield {"type": "finish", "finish_reason": choice.finish_reason}
