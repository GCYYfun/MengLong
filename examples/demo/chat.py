#!/usr/bin/env python3
"""
示例脚本，演示如何使用MengLong Agent SDK。
"""

import menglong as ml
from menglong.ml_model import Model
from menglong.ml_model.utils import user


def main():
    model = Model()
    res = model.chat(
        messages=[user("你好,你是谁？简单回复一下")],
        model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    )
    print(res)


if __name__ == "__main__":
    main()
