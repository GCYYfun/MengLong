"""
多模态功能验证脚本 (2.0)

测试 MengLong SDK 的多模态支持,包括:
- 本地图片输入 (自动转为 Base64)
- 本地文档输入 (PDF)
- 音频/视频输入
"""

import sys
import argparse
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd() / "src"))

from menglong.models.model import Model
from menglong.schemas.chat import User

# 默认测试模型
ANTHROPIC_MODEL = "anthropic/global.anthropic.claude-sonnet-4-5-20250929-v1:0"
GEMINI_MODEL = "google/gemini-3-flash-preview"

# 默认测试文件路径
BASE_DIR = Path("verify/test_files")
DEFAULT_IMAGE = BASE_DIR / "test.png"
DEFAULT_PDF = BASE_DIR / "test.pdf"
DEFAULT_AUDIO = BASE_DIR / "test.mp3"
DEFAULT_VIDEO = BASE_DIR / "test.mp4"


def test_image_local(model_name: str, image_path: str = None):
    """测试本地图片输入"""
    print("\n" + "=" * 60)
    print(f"测试: 本地图片输入 ({model_name})")
    print("=" * 60)

    path = Path(image_path or DEFAULT_IMAGE)
    if not path.exists():
        print(f"⚠️  跳过: 图片不存在: {path}")
        return None

    model = Model()
    messages = [User("请描述这张图片中看到了什么?", image=str(path))]

    try:
        print(f"发送请求到 {model_name}...")
        response = model.chat(messages, model_name)
        print(f"✅ 成功!")
        print(f"响应: {response.text[:300]}...")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_pdf_local(model_name: str, pdf_path: str = None):
    """测试本地 PDF 输入"""
    print("\n" + "=" * 60)
    print(f"测试: 本地 PDF 输入 ({model_name})")
    print("=" * 60)

    path = Path(pdf_path or DEFAULT_PDF)
    if not path.exists():
        print(f"⚠️  跳过: PDF 不存在: {path}")
        return None

    model = Model()
    messages = [User("请总结这个文档的主要内容", pdf=str(path))]

    try:
        print(f"发送请求到 {model_name}...")
        response = model.chat(messages, model_name)
        print(f"✅ 成功!")
        print(f"响应: {response.text[:300]}...")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_audio_local(model_name: str, audio_path: str = None):
    """测试本地音频输入"""
    print("\n" + "=" * 60)
    print(f"测试: 本地音频输入 ({model_name})")
    print("=" * 60)

    path = Path(audio_path or DEFAULT_AUDIO)
    if not path.exists():
        print(f"⚠️  跳过: 音频不存在: {path}")
        return None

    model = Model()
    messages = [User("请转录这段音频", audio=str(path))]

    try:
        print(f"发送请求到 {model_name}...")
        response = model.chat(messages, model_name)
        print(f"✅ 成功!")
        print(f"响应: {response.text[:300]}...")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_video_local(model_name: str, video_path: str = None):
    """测试本地视频输入"""
    print("\n" + "=" * 60)
    print(f"测试: 本地视频输入 ({model_name})")
    print("=" * 60)

    path = Path(video_path or DEFAULT_VIDEO)
    if not path.exists():
        print(f"⚠️  跳过: 视频不存在: {path}")
        return None

    model = Model()
    messages = [User("请描述这个视频的内容", video=str(path))]

    try:
        print(f"发送请求到 {model_name}...")
        response = model.chat(messages, model_name)
        print(f"✅ 成功!")
        print(f"响应: {response.text[:300]}...")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="MengLong 多模态功能验证")
    parser.add_argument("--model", type=str, default=GEMINI_MODEL, help="测试模型名称")
    parser.add_argument("--image", type=str, help="图片路径")
    parser.add_argument("--pdf", type=str, help="PDF 路径")
    parser.add_argument("--audio", type=str, help="音频路径")
    parser.add_argument("--video", type=str, help="视频路径")
    args = parser.parse_args()

    print(f"🚀 MengLong 多模态功能验证 (模型: {args.model})")

    results = {}

    # 图片测试
    results["image"] = test_image_local(args.model, args.image)

    # PDF 测试
    results["pdf"] = test_pdf_local(args.model, args.pdf)

    # 如果是 Gemini, 额外测试音视频
    if "gemini" in args.model.lower() or "google" in args.model.lower():
        results["audio"] = test_audio_local(args.model, args.audio)
        results["video"] = test_video_local(args.model, args.video)

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    for k, v in results.items():
        status = "✅ 通过" if v is True else ("❌ 失败" if v is False else "⚠️  跳过")
        print(f"{k}: {status}")


if __name__ == "__main__":
    main()
