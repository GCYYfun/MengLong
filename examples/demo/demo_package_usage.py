"""
演示如何将MengLong作为依赖安装到其他项目中

本示例展示了如何在另一个项目中:
1. 将MengLong作为依赖添加到项目
2. 使用MengLong的核心功能

运行方法:
    python examples/demo/demo_package_usage.py
"""

import os
import sys
import time


def demo_install_methods():
    """展示不同的安装方法"""
    print("MengLong安装方法示例:")
    print("\n1. 使用pip从GitHub安装:")
    print("   pip install git+https://github.com/GCYYfun/MengLong.git")

    print("\n2. 使用uv从GitHub安装(更快):")
    print("   uv pip install git+https://github.com/GCYYfun/MengLong.git")

    print("\n3. 在项目的pyproject.toml中添加依赖:")
    print(
        """   [project]
   # ...其他项目配置...
   dependencies = [
       # ...其他依赖...
       "mlong @ git+https://github.com/GCYYfun/MengLong.git",
   ]
   """
    )

    print("\n4. 在项目的requirements.txt中添加:")
    print("   mlong @ git+https://github.com/GCYYfun/MengLong.git")


def demo_basic_usage():
    """展示基本的MengLong使用方法"""
    try:
        # 尝试导入并使用MengLong
        from mlong import __version__

        print(
            f"\n成功导入MengLong! 版本: {__version__ if '__version__' in dir() else '未定义'}"
        )

        # 模拟一个简单的角色扮演对话
        print("\n模拟角色扮演对话示例:")
        print("初始化模型和智能体...")
        time.sleep(1)

        # 模拟输出，在实际集成时应使用实际代码
        print("系统: 智能体已初始化，您可以开始对话")
        print("用户: 你好，请介绍一下自己")

        # 模拟智能体思考和回复
        print("智能体正在思考", end="")
        for _ in range(3):
            time.sleep(0.5)
            print(".", end="", flush=True)
        print()

        print(
            "智能体: 你好！我是小明，一个热情友好的大学生。我喜欢音乐和旅行，平时也很享受与人交流。"
        )
        print(
            "      我的性格比较开朗乐观，遇到问题总是尽量往好的方面想。有什么我能帮你的吗？"
        )

        print("\n这只是一个模拟示例。在实际项目中，您需要配置API密钥并使用真实的模型。")

    except ImportError as e:
        print(f"\n❌ 导入MengLong失败: {e}")
        print("请确保已按照上述方法之一安装了MengLong")


def create_example_project():
    """展示如何创建一个使用MengLong的示例项目"""
    print("\n创建使用MengLong的新项目示例:")

    print("\n1. 创建项目目录结构:")
    print(
        """   my_assistant/
   ├── pyproject.toml    # 项目配置
   ├── README.md         # 项目说明
   └── my_assistant/     # 源代码目录
       ├── __init__.py
       └── assistant.py  # 使用MengLong的主要代码
   """
    )

    print("\n2. pyproject.toml内容:")
    print(
        """   [build-system]
   requires = ["setuptools>=42", "wheel"]
   build-backend = "setuptools.build_meta"

   [project]
   name = "my-assistant"
   version = "0.1.0"
   description = "一个基于MengLong的智能助手"
   requires-python = ">=3.8"
   dependencies = [
       "mlong @ git+https://github.com/GCYYfun/MengLong.git",
   ]
   """
    )

    print("\n3. assistant.py示例代码:")
    print(
        """   from mlong.model import Model
   from mlong.agent.role_play.role_play_agent import RolePlayAgent

   class MyAssistant:
       def __init__(self):
           # 初始化模型和智能体
           self.model = Model()  # 默认配置
           
           # 定义角色信息
           role_info = {
               "role": {
                   "name": "智能助手",
                   "background": "一个专业、友好的AI助手",
                   "personality": "专业、有礼貌、乐于助人"
               },
               "role_system": "你是${name}，${background}。你的性格是${personality}。"
           }
           
           # 创建智能体
           self.agent = RolePlayAgent(model=self.model, role_info=role_info)
       
       def chat(self, message):
           # 与智能体对话
           return self.agent.chat(message)
       
       def chat_stream(self, message):
           # 流式对话
           return self.agent.chat_stream(message)
   """
    )


if __name__ == "__main__":
    print("=" * 60)
    print("MengLong包使用演示")
    print("=" * 60)

    # 展示安装方法
    demo_install_methods()

    # 展示基本使用
    demo_basic_usage()

    # 展示创建使用MengLong的项目
    create_example_project()

    print("\n" + "=" * 60)
    print("演示完成！更多信息请参考MengLong文档")
    print("=" * 60)
