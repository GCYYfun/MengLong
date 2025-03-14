from mlong.world import World
from typing import Dict, Tuple, Any
import random


class TemperatureWorld(World):
    """温度调节环境演示"""

    def init(self, config: Dict[str, Any]) -> None:
        self.target_temp = config["target_temp"]
        self.current_temp = config["initial_temp"]
        self.step_count = 0

    def reset(self, seed: int) -> Dict[str, Any]:
        random.seed(seed)
        self.current_temp = random.uniform(18.0, 28.0)
        self.step_count = 0
        return self.current_state

    def step(self, action: Dict) -> Dict[str, Any]:
        adjustment = action["adjustment"]

        prev_temp = self.current_temp
        self.current_temp += adjustment
        self.trigger_event("temp_change", {"old_temp": prev_temp, "new_temp": self.current_temp})

        self.step_count += 1
        done = abs(self.current_temp - self.target_temp) < 0.5
        reward = -abs(self.current_temp - self.target_temp)
        return {
            "state": self.current_state,
            "reward": reward,
            "done": done,
            "info": {"status": "SUCCESS" if done else "CONTINUE"}
        }

    def validate_action(self, action: Dict) -> bool:
        return isinstance(action.get("adjustment"), (int, float))

    @property
    def current_state(self) -> Dict[str, Any]:
        return {
            "current_temp": self.current_temp,
            "target_temp": self.target_temp,
            "steps": self.step_count,
        }


class TemperatureAgent:
    def __init__(self, name: str):
        self.name = name

    def generate_action(self, observation: Dict) -> Dict:
        """根据观测生成温度调节动作"""
        return {
            "adjustment": random.uniform(-1.0, 1.5)
            * (observation["target_temp"] - observation["current_temp"])
        }

    def on_temp_change(self, event_type: str, data: Dict):
        print(
            f"[{self.name}] 温度变化: {data['old_temp']:.1f}℃ → {data['new_temp']:.1f}℃"
        )


if __name__ == "__main__":
    # 初始化环境
    env = TemperatureWorld()
    env.init({"initial_temp": 22.0, "target_temp": 24.0})

    # 创建Agent并订阅事件
    agent = TemperatureAgent("温控Agent")
    env.subscribe_event(agent.on_temp_change)

    # 第一次运行
    print("=== 第一次运行 ===")
    for _ in range(3):
        obs = env.reset(seed=42)
        action = agent.generate_action(obs)
        if env.validate_action(action):
            result = env.step(action)
            obs = result["state"]
            info = result["info"]
            print(f"当前状态: {env.current_state}")

    # 重置后再次运行
    print("\n=== 重置后运行 ===")
    env.reset(seed=42)  # 使用相同seed重置
    for _ in range(3):
        obs = env.current_state
        action = agent.generate_action(obs)
        if env.validate_action(action):
            result = env.step(action)
            obs = result["state"]
            info = result["info"]
            print(f"当前状态: {env.current_state}")
