#!/usr/bin/env python3
"""
示例脚本，演示如何使用MengLong Agent SDK。
"""

import menglong as mlong
from menglong import Model
from menglong.schema import user


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
    print("Normal Chat")
    print("正在向模型发送请求...")
    # 创建模型实例
    response = model.chat(
        messages=[user(content="你好,你是谁？简单回复一下")],
    )
    # 打印模型响应
    print("模型响应：", response)
    print("-" * 40)
    print(response.text)


def thinking_chat(model: Model):
    """
    演示如何使用模型进行思考聊天交互。
    Args:
        model (Model): 模型实例
    """
    print("Thinking Chat")
    print("正在向模型发送请求...")
    # 创建模型实例
    response = model.chat(
        messages=[user(content="你好,你是谁？简单回复一下")],
        # thinking={"budget_tokens": 2048, "type": "enabled"},
    )
    # 打印模型响应
    print(response)
    return response


def streaming_chat(model: Model):
    """
    演示如何使用模型进行流式聊天交互。
    Args:
        model (Model): 模型实例
    """
    print("Streaming Chat")
    print("正在向模型发送请求...")
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
            if chunk.output.delta.text:
                print(chunk.output.delta.text, end="")
            elif chunk.output.delta.reasoning:
                print(chunk.output.delta.reasoning, end="")
            elif chunk.output.start:
                print("--")
            elif chunk.output.end:
                print("\nchunk.output.end\n")
                # if chunk.output.end == "stop":
                #     print("\n--")
                # if chunk.output.end == "0":
                #     print("\n--")

    rich_print_stream_response(res)

    return res


def main():
    # 配置日志记录
    # configure_logger(log_file="chat_demo.log")
    # logger = get_logger()
    # logger.debug("初始化模型...")

    model = Model(
        "gpt-5.1",
    )

    normal_chat(model)
    # thinking_chat(model)
    # streaming_chat(model)


if __name__ == "__main__":
    main()
