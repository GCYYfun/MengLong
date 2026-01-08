import traceback
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd() / "src"))

from menglong.models.model import Model
from menglong.utils.config.config_loader import load_config

def test_real_call():
    parser = argparse.ArgumentParser(description="MengLong Real API Verification")
    parser.add_argument("--model", type=str, help="Specific model_id to test (provider/model)")
    args = parser.parse_args()

    print("🚀 MengLong Real API Call Verification")
    
    # 模拟环境或真实环境
    # 我们依赖 .configs.toml
    model = Model()
    
    test_models = []
    if args.model:
        test_models = [args.model]
    else:
        # 默认测试列表
        # test_models = [
        #     "openai/gpt-5.1",
        #     "deepseek/deepseek-chat",
        #     "aws/global.anthropic.claude-sonnet-4-5-20250929-v1:0",
        #     "anthropic/global.anthropic.claude-sonnet-4-5-20250929-v1:0",
        #     "google/gemini-3-pro-preview",
        #     "infinigence/claude-sonnet-4-20250514"
        # ]
        test_models = [
            "menglong/gemini-3-pro-preview",
            # "menglong/deepseek-chat",
            # "menglong/gpt-5.1",
            # "menglong/claude-sonnet-4-20250514",
            # "menglong/global.anthropic.claude-sonnet-4-5-20250929-v1:0",
        ]
            
    for model_id in test_models:
        print(f"\n--- Testing Model: {model_id} ---")
        try:
            
            print(f"Initiating request...")
            
            messages = [{"role": "user", "content": "Say :Hello Bro! print a picture"}]
            
            response = model.chat(messages,model_id)
            
            print(f"✅ Success!")
            print(f"Response: {response.text}")
            
        except Exception as e:
            # 如果是因为没配置 key 导致的，可以预期内失败
            if "missing" in str(e).lower() or "not found" in str(e).lower():
                print(f"⚠️ Skipped: {e}")
            else:
                print(f"❌ Failed: {e}")
                # traceback.print_exc()

if __name__ == "__main__":
    test_real_call()
