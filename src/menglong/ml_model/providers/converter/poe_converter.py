"""
Poe API 转换器实现。
"""

import traceback
import fastapi_poe as fp
from ...schema.ml_response import ChatResponse, Content, Message
from .base_converter import BaseConverter, trace_converter_method
from ....utils.log import get_logger, print_json


class PoeConverter(BaseConverter):
    """
    与 Poe API 兼容的消息转换器类。
    """

    @staticmethod
    @trace_converter_method
    def convert_request(messages):
        """将MLong消息转换为Poe兼容格式。"""
        logger = get_logger("converter.poe")

        # 验证输入
        messages = BaseConverter._validate_input_messages(
            messages, "Poe.convert_request"
        )

        poe_messages = []

        try:
            for index, message in enumerate(messages):
                logger.debug(f"处理 Poe 消息 {index}: {type(message).__name__}")

                # 处理字典格式的消息
                if isinstance(message, dict):
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
                            fp.ProtocolMessage(
                                role="system", content=message["content"]
                            )
                        )
                    else:
                        error_msg = (
                            f"不支持的消息角色 (索引 {index}): {message['role']}"
                        )
                        logger.error(error_msg)
                        raise ValueError(error_msg)

                    logger.debug(f"Poe 消息 {index}: {message['role']}")
                else:
                    error_msg = (
                        f"Poe 转换器仅支持字典格式消息 (索引 {index}): {type(message)}"
                    )
                    logger.error(error_msg)
                    raise ValueError(error_msg)

            logger.info(
                f"Poe 请求转换完成: {len(messages)} -> {len(poe_messages)} 条消息"
            )
            return poe_messages

        except Exception as e:
            logger.error(f"Poe 请求转换失败: {e}")
            print_json(
                {
                    "error": str(e),
                    "input_message_count": len(messages),
                    "processed_count": len(poe_messages),
                    "error_trace": traceback.format_exc(),
                },
                title="Poe 请求转换错误详情",
            )
            raise

    @staticmethod
    @trace_converter_method
    def normalize_response(response):
        """将Poe响应标准化为MLong的响应格式。"""
        logger = get_logger("converter.poe")

        # 验证响应
        response = BaseConverter._validate_response(response, "Poe.normalize_response")

        try:
            logger.debug(f"开始处理 Poe 响应，响应类型: {type(response).__name__}")

            # Poe 响应通常是简单的字符串格式
            if isinstance(response, str):
                content = Content(text=response)
                logger.debug("Poe 响应为字符串格式")
            else:
                # 如果不是字符串，尝试转换
                content = Content(text=str(response))
                logger.warning(
                    f"Poe 响应不是字符串格式，已转换: {type(response).__name__}"
                )

            message = Message(content=content)
            mlong_response = ChatResponse(message=message)

            logger.info("Poe 响应标准化完成")
            return mlong_response

        except Exception as e:
            logger.error(f"Poe 响应标准化失败: {e}")
            print_json(
                {
                    "error": str(e),
                    "response_type": type(response).__name__,
                    "response_content": (
                        str(response)[:200] + "..."
                        if len(str(response)) > 200
                        else str(response)
                    ),
                    "error_trace": traceback.format_exc(),
                },
                title="Poe 响应标准化错误详情",
            )
            raise
