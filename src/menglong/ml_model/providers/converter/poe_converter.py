"""
Poe API 转换器实现。
"""

import fastapi_poe as fp
from ...schema.ml_response import ChatResponse, Content, Message
from .base_converter import BaseConverter


class PoeConverter(BaseConverter):
    """
    与 Poe API 兼容的消息转换器类。
    """

    @staticmethod
    def convert_request(messages):
        """将MLong消息转换为Poe兼容格式。"""
        poe_messages = []
        for message in messages:
            if message["role"] == "user":
                poe_messages.append(
                    fp.ProtocolMessage(role="user", content=message["content"])
                )
            elif message["role"] == "assistant":
                poe_messages.append(
                    fp.ProtocolMessage(role="bot", content=message["content"])
                )
            elif message["role"] == "system":
                poe_messages.append(
                    fp.ProtocolMessage(role="system", content=message["content"])
                )
        return poe_messages

    @staticmethod
    def normalize_response(response):
        """将Poe响应标准化为MLong的响应格式。"""
        content = Content(text_content=response)
        message = Message(content=content)
        mlong_response = ChatResponse(message=message)
        return mlong_response
