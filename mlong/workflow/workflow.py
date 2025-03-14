import json
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class WorkflowStep:
    task_id: str  # 步骤名称
    method: str  # 对应的方法名
    description: str  # 步骤描述
    prompt: str  # 步骤提示
    variables: Dict[str, Any]  # 步骤变量


class Workflow:
    def __init__(self, config_file: Optional[str] = None):
        self.workflow: List[WorkflowStep] = []
        self.load_workflow(config_file)

    def load_workflow(self, config_file: str):
        """从配置文件加载工作流程"""
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)  # 改为使用yaml解析
            self.workflow = [WorkflowStep(**step) for step in config["workflow"]]

    def execute_workflow(
        self, agent: Any, inputs: List = None, debug=False
    ) -> Dict[str, Any]:
        """执行工作流程"""
        if debug:
            print("当前 workflow 步骤:",len(self.workflow))
        for step in self.workflow:
            # 处理prompt模板变量
            formatted_prompt = step.prompt.format_map({**step.variables})
            if debug:
                print("🔍 检查当前要执行的workflow...")
                print(formatted_prompt)

            # 准备方法参数
            method_args = {"input_messages": formatted_prompt}

            # 执行agent方法
            method = getattr(agent, step.method)
            result = method(**method_args)
            if debug:
                print("🔍 检查当前发送的context...")
                print(agent.context_manager.context)

        return result
