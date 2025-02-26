# MengLong 核心模块

本目录包含朦胧框架的核心模块，提供了对大语言模型的抽象和各种功能实现。

## 模块结构

- **model.py**: 模型抽象层，统一管理不同LLM模型的接口
- **provider.py**: 提供商管理器，管理不同的模型提供商

## 子目录说明

- **agent/**: 智能体实现，包括基础智能体和特定场景的智能体（如角色扮演智能体）
- **memory/**: 记忆系统实现，包括短期记忆、工作记忆和情节记忆
- **prompts/**: 提示模板管理，为不同场景提供专门的提示模板
- **providers/**: 不同模型提供商的具体实现
- **retrieval/**: 检索相关功能，包括搜索和向量检索
- **tools/**: 工具集成，扩展智能体的能力
- **types/**: 类型定义，确保接口一致性
- **utils/**: 工具函数，提供通用功能

## 模型支持

当前支持的模型包括：

### OpenAI
- GPT-4 系列

### Anthropic
- Claude 3.5
- Claude 3.7

### AWS
- Claude 3.5 (通过AWS Bedrock)
- Nova Pro

## 使用示例

```python
# 创建模型实例
modelconfig = {
    'openai': {
        'GPT4': {
            'model_name': 'openai',
            'model_type': 'GPT4',
            'model_path': 'openai/GPT4',
            'tokenizer_path': 'openai/GPT4',
            'model_config': 'openai/GPT4',
            'tokenizer_config': 'openai/GPT4',
            'model': None,
            'tokenizer': None
        }
    }
}
model = Model(modelid='openai.GPT4', modelconfig=modelconfig)

# 使用模型生成内容
response = model.generate("请解释一下人工智能的基本概念")
print(response)
```

## Agent系统架构

Agent系统的核心组件包括：

- **Task Manager**: 任务管理器，负责任务的分配和监控
- **Task Queue**: 任务队列，管理待执行的任务
- **Task Scheduler**: 任务调度器，决定任务的执行顺序
- **Task Monitor**: 任务监控器，监控任务的执行状态
- **Task Executor**: 任务执行器，负责具体任务的执行
- **Task Logger**: 任务日志记录器，记录任务的执行过程和结果
