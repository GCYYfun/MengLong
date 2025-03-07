import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class WorkflowStep:
    name: str  # 步骤名称
    method: str  # 对应的方法名
    description: str  # 步骤描述
    input_fields: List[str]  # 输入字段
    output_fields: List[str]  # 输出字段
    condition: Optional[str] = None  # 执行条件

class WorkflowEngine:
    def __init__(self):
        self.workflow: List[WorkflowStep] = []
        self.load_default_workflow()
    
    def load_default_workflow(self):
        """加载默认的工作流程配置"""
        self.workflow = [
            WorkflowStep(
                name="observe",
                method="observe",
                description="观察和分析输入信息",
                input_fields=["env_status"],
                output_fields=["observation"],
            ),
            WorkflowStep(
                name="process",
                method="retrieve",
                description="处理和检索相关信息",
                input_fields=["observation"],
                output_fields=["retrieved_info"],
            ),
            WorkflowStep(
                name="think",
                method="thinking",
                description="思考和制定方案",
                input_fields=["env_status", "retrieved_info"],
                output_fields=["plan"],
            ),
            WorkflowStep(
                name="reflect",
                method="reflect",
                description="检查和评估方案",
                input_fields=["plan"],
                output_fields=["decision"],
            ),
            WorkflowStep(
                name="execute",
                method="execute",
                description="执行最终方案",
                input_fields=["decision"],
                output_fields=["result"],
            ),
        ]
    
    def load_workflow_from_config(self, config_file: str):
        """从配置文件加载工作流程"""
        with open(config_file, 'r') as f:
            config = json.load(f)
            self.workflow = [
                WorkflowStep(**step) for step in config['workflow']
            ]
    
    def execute_workflow(self, agent: Any, initial_input: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流程"""
        context = initial_input.copy()
        
        for step in self.workflow:
            # 检查条件
            if step.condition and not eval(step.condition, {}, context):
                continue
                
            # 准备输入参数
            method_args = {field: context.get(field) for field in step.input_fields}
            
            # 执行方法
            method = getattr(agent, step.method)
            result = method(**method_args)
            
            # 更新上下文
            if isinstance(result, tuple):
                for field, value in zip(step.output_fields, result):
                    context[field] = value
            else:
                context[step.output_fields[0]] = result
        
        return context