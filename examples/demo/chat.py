#!/usr/bin/env python3
"""
示例脚本，演示如何使用MengLong Agent SDK。
"""

import menglong as ml
from menglong.ml_model import Model
from menglong.ml_model.schema import user
from menglong.utils.log import (
    print_message,
    print_rule,
    MessageType,
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
    print_rule("Normal Chat", style="green")
    print_message("正在向模型发送请求...", MessageType.INFO)
    # 创建模型实例
    response = model.chat(
        messages=[user(content="你好,你是谁？简单回复一下")], debug=True
    )
    # 打印模型响应
    print_message(
        response.message.content.text,
        MessageType.AGENT,
        title="AI Assistant",
        subtitle=f"{model.provider}/{model.model_id}",
        panel=True,
    )
    return response


def thinking_chat(model: Model):
    """
    演示如何使用模型进行思考聊天交互。
    Args:
        model (Model): 模型实例
    """
    print_rule("Thinking Chat", style="green")
    print_message("正在向模型发送请求...", MessageType.INFO)
    # 创建模型实例
    response = model.chat(
        messages=[user(content="你好,你是谁？简单回复一下")],
        thinking={"budget_tokens": 2048, "type": "enabled"},
    )
    # 打印模型响应
    print_message(response, MessageType.AGENT, title="AI Assistant", use_panel=True)
    return response


def streaming_chat(model: Model):
    """
    演示如何使用模型进行流式聊天交互。
    Args:
        model (Model): 模型实例
    """
    print_rule("Streaming Chat", style="green")
    print_message("正在向模型发送请求...", MessageType.INFO)
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
                print_message(chunk.message.delta.text, end="")
            elif chunk.message.delta.reasoning:
                print_message(chunk.message.delta.reasoning, end="")
            elif chunk.message.start_reason:
                print_message("--")
            elif chunk.message.finish_reason:
                if chunk.message.finish_reason == "stop":
                    print_message("\n--")
                if chunk.message.finish_reason == "0":
                    print_message("\n--")

    rich_print_stream_response(res)

    return res


def main():
    # 配置日志记录
    # configure_logger(log_file="chat_demo.log")
    # logger = get_logger()
    # logger.debug("初始化模型...")

    model = Model(model_id="claude-3-7-sonnet-20250219")

    normal_chat(model)
    # thinking_chat(model)
    # streaming_chat(model)


if __name__ == "__main__":
    main()
