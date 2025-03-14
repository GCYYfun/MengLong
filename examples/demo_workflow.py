
from dataclasses import dataclass
import time
import os

from mlong.workflow.workflow import Workflow
from mlong.agent.role import RoleAgent

class DemoAgent:
    def analyze_requirements(self, task: str) -> dict:
        print(f"\n🔍 正在分析需求: {task}")
        time.sleep(1)
        return {
            'framework': 'FastAPI',
            'database': 'PostgreSQL',
            'auth': 'JWT'
        }

    def generate_code(self, spec: dict) -> str:
        print(f"\n💻 根据规范生成代码: {spec}")
        time.sleep(2)
        return """
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    username: str
    email: str

@app.post("/users/")
def create_user(user: User):
    return {"message": "User created successfully"}
"""

if __name__ == "__main__":
    role_config = {
        "id":"Alice",
        "role_system": "你是一个中国${gender}性，你的名字叫${name}。\n\n${topic}\n\n${daily_logs}",
        "role_info": {
            "name": "Alice",
            "gender": "女",
            "age": "18"
        },
        "role_var": {
            "topic": "",
            "daily_logs": ""
        }
    }
    agent = RoleAgent(role_config=role_config)
    workflow = Workflow(config_file=os.path.join(os.path.dirname(__file__), "workflow_config.yaml"))
    
    # debug
    print("🔍 检查agent system prompt...")
    print(agent.system_prompt)

    print("🚀 开始执行工作流...")
    result = workflow.execute_workflow(
        agent=agent,
        debug=True
    )
    
    print("\n✅ 最终生成的代码:")
    print(result)