"""
AWS API 转换器实现。
"""

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
from .base_converter import BaseConverter


class AwsConverter(BaseConverter):
    """
    与 AWS API 兼容的消息转换器类。
    """

    reasoning = False
    tool = False

    @staticmethod
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
        system_messages = []
        prompt_messages = []
        for message in messages:
            if isinstance(message, SystemMessage):
                system_messages.append({"text": message.content})
            elif isinstance(message, UserMessage):
                if message.tool_id is not None:
                    # 处理用户消息的字符串内容
                    prompt_messages.append(
                        {
                            "role": message.role,
                            "content": [
                                {
                                    "toolResult": {
                                        "toolUseId": (message.tool_id),
                                        "content": [
                                            {"json": {"data": message.content}}
                                        ],
                                    }
                                }
                            ],
                        }
                    )
                else:
                    prompt_messages.append(
                        {"role": message.role, "content": [{"text": message.content}]}
                    )
            elif isinstance(message, AssistantMessage):
                prompt_messages.append(
                    {"role": message.role, "content": message.content}
                )
            elif isinstance(message, Message):
                # 处理助手消息的列表内容
                content = []
                if message.content.text is not None:
                    content.append({"text": message.content.text})
                if message.tool_desc is not None:
                    for item in message.tool_desc:
                        content.append(
                            {
                                "toolUse": {
                                    "toolUseId": item.id,
                                    "name": item.name,
                                    "input": item.arguments,
                                }
                            }
                        )
                prompt_messages.append({"role": "assistant", "content": content})
            else:
                raise ValueError(f"Unsupported message type: {type(message)}")
        return system_messages, prompt_messages

    @staticmethod
    def normalize_response(response):
        """将AWS响应标准化为MLong的响应格式。"""
        # print("response:", response) # for debug
        output = response.get("output")
        content = Content(text=None)
        # message = Message(content=content, finish_reason=response["stopReason"])
        if AwsConverter.reasoning:  # 纯推理
            content.reasoning = output["message"]["content"][0]["reasoningContent"][
                "reasoningText"
            ]["text"]
            content.text = output["message"]["content"][1]["text"]
            message = Message(
                content=content,
                finish_reason=response["stopReason"],
            )
        elif response["stopReason"] == "tool_use":
            index = 0
            if "text" in output["message"]["content"][index]:
                content.text = output["message"]["content"][index]["text"]
                index += 1
            desc = [
                ToolDesc(
                    id=item["toolUse"]["toolUseId"],
                    type="tool_use",
                    name=item["toolUse"]["name"],
                    arguments=item["toolUse"]["input"],
                )
                for item in output["message"]["content"][index:]
            ]
            message = Message(
                content=content,
                finish_reason=response["stopReason"],
                tool_desc=desc,
            )
        else:
            content.text = output["message"]["content"][0]["text"]
            message = Message(
                content=content,
                finish_reason=response["stopReason"],
            )

        usage = Usage(
            input_tokens=response.get("usage", {}).get("inputTokens", 0),
            output_tokens=response.get("usage", {}).get("outputTokens", 0),
            total_tokens=response.get("usage", {}).get("totalTokens", 0),
        )

        mlong_response = ChatResponse(
            message=message, model=response.get("modelId"), usage=usage
        )
        return mlong_response

    @staticmethod
    def normalize_stream_response(
        response_stream,
    ) -> Generator:
        """将AWS流式响应标准化为MLong的响应格式。"""
        # 返回生成器
        for chunk in response_stream.get("stream", []):
            # 处理流式响应
            delta = ContentDelta()
            start = None
            finish = None
            usage = None
            # for debug
            # print(chunk)
            # 处理不同类型的消息
            match chunk:
                case {"contentBlockDelta": block}:
                    # 处理文本内容
                    if block.get("delta").get("text") is not None:
                        delta.text = block.get("delta").get("text")
                    # 处理推理内容
                    if block.get("delta").get("reasoningContent") is not None:
                        delta.reasoning = (
                            block.get("delta").get("reasoningContent").get("text")
                        )
                    # # 处理工具调用
                    # if block.get("delta").get("toolResult") is not None:
                    #     delta.tool_result = block.get("delta").get("toolResult")
                    #     delta.tool_result.tool_use_id = (
                    #         block.get("delta").get("toolResult").get("toolUseId")
                    #     )
                case {"messageStart": message_start}:
                    # 处理推理内容
                    start = message_start.get("role")
                    pass
                case {"contentBlockStop": content_stop}:
                    # 处理内容块停止
                    content_stop_index = content_stop.get("contentBlockIndex")
                    finish = f"{content_stop_index}"
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
