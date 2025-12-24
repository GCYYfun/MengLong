import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Callable

# Add src to path
sys.path.append(str(Path.cwd() / "src"))

from menglong.models.model import Model
from menglong.components.tool_component import tool
from menglong.schemas.chat import Context, Assistant, Tool

# --- 1. 定义交互式工具 ---

@tool
def get_weather(city: str):
    """
    Get the weather of a specific city.
    
    Args:
        city: The name of the city.
    """
    print(f"DEBUG: Executing get_weather for {city}...")
    return {"city": city, "temperature": 25, "unit": "Celsius", "condition": "Sunny"}

class Calculator:
    def __init__(self, precision: int = 2):
        self.precision = precision

    @tool
    def add(self, a: float, b: float):
        """
        Add two numbers.
        
        Args:
            a: First number.
            b: Second number.
        """
        print(f"DEBUG: Executing add({a}, {b})...")
        return round(a + b, self.precision)

    @classmethod
    @tool
    def multiply(cls, x: float, y: float):
        """
        Multiply two numbers.
        
        Args:
            x: First factor.
            y: Second factor.
        """
        print(f"DEBUG: Executing multiply({x}, {y})...")
        return x * y

# --- 2. 闭环执行逻辑 ---

def run_loop(model: Model, model_id: str, prompt: str, tools: List[Callable]):
    print(f"\n--- Round-trip Test on: {model_id} ---")
    print(f"User Query: {prompt}")
    
    # 使用 Context 管理对话状态
    ctx = Context().user(prompt)
    
    # 建立工具映射表，用于执行
    tool_map = {t.__name__: t for t in tools}
    
    # 第一步：获取工具调用建议
    response = model.chat(ctx, model=model_id, tools=tools)
    ctx.add(Assistant(content=response.text, tool_calls=[tc.model_dump() for tc in response.tool_calls] if response.tool_calls else None))
    
    if response.tool_calls:
        print(f"🛠️  Model suggested {len(response.tool_calls)} tool call(s).")
        
        # 执行工具
        for tc in response.tool_calls:
            print(f"   -> Calling {tc.name} with {tc.arguments}")
            func = tool_map.get(tc.name)
            if func:
                result = func(**tc.arguments)
                print(f"   <- Result: {result}")
                # 将结果回传 (OpenAI/Anthropic 风格：需要 tool_use_id 对齐)
                ctx.tool(tool_id=tc.id, content=json.dumps(result), name=tc.name)
            else:
                print(f"   ❌ Tool {tc.name} not found in map!")
        
        # 第二步：获取最终总结
        print("Waiting for final summary...")
        final_response = model.chat(ctx, model=model_id, tools=tools)
        print(f"✅ Final Summary: {final_response.text}")
    else:
        print(f"✅ Direct Response: {response.text}")

def test_tool_call():
    parser = argparse.ArgumentParser(description="MengLong Real Tool Loop Verification")
    parser.add_argument("--model", type=str, help="Specific model_id to test")
    args = parser.parse_args()

    model = Model()
    calc = Calculator(precision=4)
    tools = [get_weather, calc.add, Calculator.multiply]
    
    test_models = []
    if args.model:
        test_models = [args.model]
    else:
        # 默认测试列表
        test_models = [
            "openai/gpt-5.1",
            "deepseek/deepseek-chat",
            "aws/global.anthropic.claude-sonnet-4-5-20250929-v1:0",
            # "anthropic/claude-3-5-sonnet-20240620",
            "anthropic/global.anthropic.claude-sonnet-4-5-20250929-v1:0",
            "google/gemini-3-pro-preview",
            "infinigence/claude-sonnet-4-20250514"
        ]
            
    for model_id in test_models:
        try:
            # 测试用例 1：计算
            run_loop(model, model_id, "What is 1.23456 + 2.34567?", tools)
            # 测试用例 2：天气
            run_loop(model, model_id, "What's the weather like in Paris?", tools)
        except Exception as e:
            if "missing" in str(e).lower() or "not found" in str(e).lower() or "not allowed" in str(e).lower():
                print(f"⚠️  Skipped {model_id}: {e}")
            else:
                print(f"❌ Failed {model_id}: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    test_tool_call()
