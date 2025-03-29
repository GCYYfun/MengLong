"""
AWS API 转换器实现。
"""

from mlong.model_interface.schema.response import (
    ChatResponse,
    Content,
    Usage,
    Message,
    ContentDelta,
    StreamMessage,
    ChatStreamResponse,
)
from .base_converter import BaseConverter


class AwsConverter(BaseConverter):
    """
    与 AWS API 兼容的消息转换器类。
    """

    reasoning = False

    @staticmethod
    def convert_request(messages):
        """将MLong消息转换为AWS兼容格式。"""
        pass

    @staticmethod
    def normalize_response(response):
        """将AWS响应标准化为MLong的响应格式。"""
        content = Content(text_content="")
        if AwsConverter.reasoning:
            content.reasoning_content = response["output"]["message"]["content"][0][
                "reasoningContent"
            ]["reasoningText"]["text"]
            content.text_content = response["output"]["message"]["content"][1]["text"]
        else:
            content.text_content = response["output"]["message"]["content"][0]["text"]

        message = Message(content=content, finish_reason=response.get("finishReason"))

        usage = Usage(
            input_tokens=response.get("usage", {}).get("promptTokens", 0),
            output_tokens=response.get("usage", {}).get("completionTokens", 0),
            total_tokens=response.get("usage", {}).get("totalTokens", 0),
        )

        mlong_response = ChatResponse(
            message=message, model=response.get("modelId"), usage=usage
        )
        return mlong_response

    @staticmethod
    def normalize_stream_response(response_stream):
        """将AWS流式响应标准化为MLong的响应格式。"""
        # 返回生成器
        for chunk in response_stream.get("stream", []):
            # 处理流式响应
            delta = ContentDelta()
            start = None
            finish = None
            usage = None
            # 处理不同类型的消息
            match chunk:
                case {"contentBlockDelta": block}:
                    # 处理文本内容
                    delta.text_content = block.get("delta").get("text")
                case {"reasoningContent": _}:
                    AwsConverter.reasoning = True
                case {"messageStart": message_start}:
                    # 处理推理内容
                    start = message_start.get("role")
                    pass
                case {"messageStop": message_stop}:
                    if message_stop.get("stopReason") == "end_turn":
                        finish = "end_turn"
                case {"metadata": metadata}:
                    # 处理元数据
                    usage = Usage(
                        input_tokens=metadata.get("usage").get("inputTokens", 0),
                        output_tokens=metadata.get("usage").get("outputTokens", 0),
                        total_tokens=metadata.get("usage").get("totalTokens", 0),
                    )
                case _:
                    pass

            # if AwsConverter.reasoning:
            #     delta = ContentDelta(
            #         text_content=chunk.get("content"),
            #         reasoning_content=chunk.get("reasoningContent"),
            #     )
            # else:

            #     delta = ContentDelta(
            #         text_content=chunk.get("contentBlockDelta")
            #         .get("delta")
            #         .get("text"),
            #         reasoning_content=None,
            #     )
            message = StreamMessage(
                delta=delta,
                start_reason=start,
                finish_reason=finish,
            )
            yield ChatStreamResponse(message=message, model_id=None, usage=usage)
