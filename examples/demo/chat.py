#!/usr/bin/env python3
"""
示例脚本，演示如何使用MengLong Agent SDK。
"""

import menglong as ml
from menglong.ml_model import Model
from menglong.ml_model.schema import user
from menglong.utils.log import (
    rich_print,
    rich_print_rule,
    rich_print_stream,
    RichMessageType,
    configure_logger,
    get_logger,
)


# normal chat
# thinking chat
# straming chat
# tool use
#


def normal_chat(model: Model):
    """
    演示如何使用模型进行正常的聊天交互。
    Args:
        model (Model): 模型实例
    """
    rich_print_rule("Normal Chat", style="green")
    rich_print("正在向模型发送请求...", RichMessageType.INFO)
    # 创建模型实例
    response = model.chat(
        messages=[user(content="你好,你是谁？简单回复一下")],
    )
    # 打印模型响应
    rich_print(
        response,
        RichMessageType.AGENT,
        title="AI Assistant",
        subtitle=model.model_id,
        use_panel=True,
    )
    return response


def thinking_chat(model: Model):
    """
    演示如何使用模型进行思考聊天交互。
    Args:
        model (Model): 模型实例
    """
    rich_print_rule("Thinking Chat", style="green")
    rich_print("正在向模型发送请求...", RichMessageType.INFO)
    # 创建模型实例
    response = model.chat(
        messages=[user(content="你好,你是谁？简单回复一下")],
        thinking={"budget_tokens": 2048, "type": "enabled"},
    )
    # 打印模型响应
    rich_print(response, RichMessageType.AGENT, title="AI Assistant", use_panel=True)
    return response


def streaming_chat(model: Model):
    """
    演示如何使用模型进行流式聊天交互。
    Args:
        model (Model): 模型实例
    """
    rich_print_rule("Streaming Chat", style="green")
    rich_print("正在向模型发送请求...", RichMessageType.INFO)
    # 创建模型实例
    res = model.chat(
        messages=[user(content="你好,你是谁？简单回复一下")],
        stream=True,
        # thinking={"budget_tokens": 2048, "type": "enabled"},
    )

    def rich_print_stream_response(res):
        # 处理流式响应
        for chunk in res:
            # 打印每个块的内容
            # rich_print_stream(
            #     chunk, RichMessageType.AGENT, title="AI Assistant", use_panel=True
            # )
            if chunk.message.delta.text:
                rich_print(chunk.message.delta.text, end="")
            elif chunk.message.delta.reasoning:
                rich_print(chunk.message.delta.reasoning, end="")
            elif chunk.message.start_reason:
                rich_print("--")
            elif chunk.message.finish_reason:
                if chunk.message.finish_reason == "stop":
                    rich_print("\n--")
                if chunk.message.finish_reason == "0":
                    rich_print("\n--")

    rich_print_stream_response(res)

    return res


def main():
    # 配置日志记录
    # configure_logger(log_file="chat_demo.log")
    # logger = get_logger()
    # logger.debug("初始化模型...")

    model = Model(
        model_id="deepseek-r1",
    )

    normal_chat(model)
    # thinking_chat(model)
    # streaming_chat(model)


if __name__ == "__main__":
    main()
