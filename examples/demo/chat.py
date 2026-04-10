#!/usr/bin/env python3
"""
MengLong SDK Demo
=================
演示 MengLong SDK 的核心功能，通过参数选择要运行的场景：

  python chat.py                      # 默认运行所有演示
  python chat.py --demo chat          # 仅运行普通聊天
  python chat.py --demo stream        # 仅运行流式聊天
  python chat.py --demo thinking      # 仅运行推理模式（thinking）
  python chat.py --demo tool          # 仅运行工具调用
  python chat.py --model deepseek/deepseek-chat --demo tool
"""

import argparse
import json

from menglong import Model, Context, Assistant, Tool, tool


# =============================================================================
#  工具定义（tool call 演示用）
# =============================================================================


@tool
def get_weather(city: str) -> dict:
    """
    Get the current weather for a given city.

    Args:
        city: The name of the city.
    """
    return {
        "city": city,
        "temperature": 22,
        "unit": "Celsius",
        "condition": "Sunny",
        "humidity": 60,
    }


@tool
def calculate(expression: str) -> str:
    """
    Evaluate a simple arithmetic expression and return the result.

    Args:
        expression: A math expression string, e.g. '1 + 2 * 3'.
    """
    try:
        result = eval(expression, {"__builtins__": {}})  # noqa: S307
        return str(result)
    except Exception as e:
        return f"Error: {e}"


# =============================================================================
#  演示函数
# =============================================================================


def demo_chat(model: Model):
    """普通聊天 —— 单轮问答"""
    print("\n" + "=" * 50)
    print("  📝  普通聊天（Normal Chat）")
    print("=" * 50)

    ctx = Context()
    ctx.system("你是一位简洁友好的 AI 助手，回复请控制在 2 句话以内。")
    ctx.user("你好，你是谁？")

    response = model.chat(messages=ctx)
    print(f"[assistant] {response.text}")


def demo_stream(model: Model):
    """流式聊天 —— 实时打印 token"""
    print("\n" + "=" * 50)
    print("  ⚡  流式聊天（Stream Chat）")
    print("=" * 50)

    ctx = Context()
    ctx.system("你是一位简洁友好的 AI 助手，回复请控制在 2 句话以内。")
    ctx.user("用一句话介绍一下量子计算。")

    print("[assistant] ", end="", flush=True)
    for chunk in model.stream_chat(messages=ctx):
        if chunk.output is None:
            continue
        if chunk.output.delta and chunk.output.delta.text:
            print(chunk.output.delta.text, end="", flush=True)
        elif chunk.output.end:
            print()  # 换行


def demo_tool(model: Model):
    """工具调用 —— 两轮对话（tool_calls → tool result → 最终回答）"""
    print("\n" + "=" * 50)
    print("  🛠️   工具调用（Tool Call）")
    print("=" * 50)

    tools = [get_weather, calculate]

    # ── 测试用例列表 ──────────────────────────────────────────────
    test_cases = [
        "上海今天的天气怎么样？",
        "帮我算一下 (12.5 + 7.3) * 4",
    ]

    for prompt in test_cases:
        print(f"\n[user] {prompt}")

        ctx = Context()
        ctx.system("你是一位使用工具解决问题的 AI 助手。")
        ctx.user(prompt)

        # 第一轮：获取工具调用建议
        response = model.chat(messages=ctx, tools=tools)

        if not response.tool_calls:
            print(f"[assistant] {response.text}")
            continue

        # 把 assistant 工具请求写回 Context
        ctx.add(
            Assistant(
                content=response.text,
                tool_calls=[tc.model_dump() for tc in response.tool_calls],
            )
        )

        # 执行工具并写回结果
        tool_map = {get_weather.__name__: get_weather, calculate.__name__: calculate}
        for tc in response.tool_calls:
            func = tool_map.get(tc.name)
            if func:
                result = func(**tc.arguments)
                print(f"  → 调用工具 [{tc.name}]，参数: {tc.arguments}")
                print(f"  ← 工具结果: {result}")
                ctx.tool(tool_id=tc.id, content=json.dumps(result, ensure_ascii=False))

        # 第二轮：获取最终回答
        final = model.chat(messages=ctx)
        print(f"[assistant] {final.text}")


def demo_thinking(model: Model):
    """推理模式 —— 展示 reasoning 推理链 + 最终回答

    默认使用 deepseek/deepseek-reasoner（原生支持）。
    Claude 系列可通过 thinking={"type":"enabled","budget_tokens":2048} 参数开启。
    """
    print("\n" + "=" * 50)
    print("  🧠  推理模式（Thinking / Reasoning）")
    print("=" * 50)

    # 优先使用 DeepSeek Reasoner，若调用方传入了其他模型则以传入为准
    thinking_model = Model(default_model_id="deepseek/deepseek-reasoner")

    ctx = Context()
    ctx.system("你是善于逻辑推理的 AI 助手，请展示完整的思考过程。")
    ctx.user("一个班有 30 个学生，其中 2/5 是女生，男生比女生多几人？")

    print("[thinking] ", end="", flush=True)
    in_answer = False
    for chunk in thinking_model.stream_chat(messages=ctx):
        if chunk.output is None:
            continue
        delta = chunk.output.delta
        if delta:
            if delta.reasoning:
                print(delta.reasoning, end="", flush=True)
            if delta.text:
                if not in_answer:
                    print("\n[assistant] ", end="", flush=True)
                    in_answer = True
                print(delta.text, end="", flush=True)
        if chunk.output.end:
            print()


# =============================================================================
#  入口
# =============================================================================

DEMOS = {
    "chat": demo_chat,
    "stream": demo_stream,
    "thinking": demo_thinking,
    "tool": demo_tool,
}


def main():
    parser = argparse.ArgumentParser(
        description="MengLong SDK Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--model",
        "-m",
        default=None,
        help="模型 ID，格式 'provider/model-name'，默认使用配置文件中的 default model",
    )
    parser.add_argument(
        "--demo",
        "-d",
        choices=list(DEMOS.keys()) + ["all"],
        default="all",
        help="要运行的演示场景（默认 all）",
    )
    args = parser.parse_args()

    model = Model(default_model_id=args.model) if args.model else Model()

    to_run = list(DEMOS.values()) if args.demo == "all" else [DEMOS[args.demo]]
    for fn in to_run:
        try:
            fn(model)
        except Exception as e:
            print(f"\n[ERROR] {fn.__name__} 运行失败: {e}")

    print("\n✅ Demo 完成")


if __name__ == "__main__":
    main()
