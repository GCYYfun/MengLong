import traceback
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd() / "src"))

from menglong.models.model import Model
from menglong.utils.config.config_loader import load_config


def test_parameter_mapping():
    """测试 Google Provider 的参数映射功能"""
    print("🧪 Google Provider 参数映射测试\n")

    model = Model()
    # 使用直接的 Google provider，而不是 MengLong proxy
    model_id = "google/gemini-2.0-flash-exp"

    # 测试 1: max_tokens 参数映射
    print("=" * 60)
    print("测试 1: max_tokens 参数映射")
    print("=" * 60)
    try:
        messages = [{"role": "user", "content": "请写一篇关于人工智能的文章"}]

        print(f"📤 发送请求: max_tokens=50")
        response = model.chat(messages, model_id, max_tokens=50)

        print(f"✅ 成功!")
        print(f"📊 响应长度: {len(response.text)} 字符")
        print(f"📝 响应内容: {response.text[:100]}...")
        if response.usage:
            print(f"🔢 Token 使用: {response.usage.output_tokens} tokens")

    except Exception as e:
        print(f"❌ 失败: {e}")
        traceback.print_exc()

    # 测试 2: temperature 参数
    print("\n" + "=" * 60)
    print("测试 2: temperature 参数")
    print("=" * 60)
    try:
        messages = [{"role": "user", "content": "说一句话"}]

        print(f"📤 发送请求: temperature=0.1 (低随机性)")
        response1 = model.chat(messages, model_id, temperature=0.1, max_tokens=30)

        print(f"✅ 成功!")
        print(f"📝 响应 1: {response1.text}")

        print(f"\n📤 发送请求: temperature=1.5 (高随机性)")
        response2 = model.chat(messages, model_id, temperature=1.5, max_tokens=30)

        print(f"✅ 成功!")
        print(f"📝 响应 2: {response2.text}")

    except Exception as e:
        print(f"❌ 失败: {e}")
        traceback.print_exc()

    # 测试 3: top_p 参数
    print("\n" + "=" * 60)
    print("测试 3: top_p 参数")
    print("=" * 60)
    try:
        messages = [{"role": "user", "content": "用一句话描述春天"}]

        print(f"📤 发送请求: top_p=0.5")
        response = model.chat(messages, model_id, top_p=0.5, max_tokens=30)

        print(f"✅ 成功!")
        print(f"📝 响应: {response.text}")

    except Exception as e:
        print(f"❌ 失败: {e}")
        traceback.print_exc()

    # 测试 4: 组合参数
    print("\n" + "=" * 60)
    print("测试 4: 组合参数 (max_tokens + temperature + top_p)")
    print("=" * 60)
    try:
        messages = [{"role": "user", "content": "Hello! How are you?"}]

        print(f"📤 发送请求: max_tokens=20, temperature=0.7, top_p=0.9")
        response = model.chat(
            messages, model_id, max_tokens=20, temperature=0.7, top_p=0.9
        )

        print(f"✅ 成功!")
        print(f"📝 响应: {response.text}")
        if response.usage:
            print(f"🔢 Token 使用: {response.usage.output_tokens} tokens (应该 ≤ 20)")

    except Exception as e:
        print(f"❌ 失败: {e}")
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("✨ 测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    test_parameter_mapping()
