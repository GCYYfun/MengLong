# Prompts 提示模板模块

prompts 模块管理框架中使用的各种提示模板，为不同场景提供专门优化的提示内容，确保模型生成高质量、一致性的输出。

## 模块结构

- **code/**: 代码相关提示模板
- **role_play/**: 角色扮演相关提示模板
  - **short_term_memory.json**: 短期记忆提示模板
  - **template.yaml**: 角色扮演基础模板

## 提示模板类型

### 代码相关提示 (code/)

针对代码生成、分析、调试等任务的专用提示模板，包括：
- 代码生成提示
- 代码审查提示
- 调试辅助提示
- 代码解释提示

### 角色扮演提示 (role_play/)

支持角色扮演场景的专用提示模板，包括：
- 角色定义模板
- 对话引导模板
- 记忆整合模板
- 多角色互动模板

## 提示模板格式

提示模板支持多种格式：

- **YAML 格式**: 适合结构化复杂的提示模板
- **JSON 格式**: 适合需要程序化处理的模板
- **纯文本格式**: 适合简单的提示模板

所有模板都支持变量插值，使用`${variable}`语法可以在运行时替换变量。

## 使用示例

### 角色扮演模板使用

```python
from mlong.model import Model
from mlong.agent.role_play.role_play_agent import RolePlayAgent
import yaml

# 加载模板
with open("mlong/prompts/role_play/template.yaml", "r") as f:
    template = yaml.safe_load(f)

# 创建模型
model = Model()

# 自定义角色信息
role_info = {
    "name": "医生李",
    "background": "一位经验丰富的内科医生，从医20年",
    "personality": "耐心、专业、关心患者"
}

# 使用模板创建角色扮演智能体
agent = RolePlayAgent(
    model=model,
    template=template,
    role_info=role_info
)

# 与角色对话
response = agent.chat("我最近总是感到头晕，这可能是什么原因？")
print(response)
```

### 短期记忆模板使用

```python
import json
from mlong.memory.short_term_memory import ShortTermMemory

# 加载短期记忆模板
with open("mlong/prompts/role_play/short_term_memory.json", "r") as f:
    memory_template = json.load(f)

# 使用模板初始化记忆系统
memory = ShortTermMemory(
    max_tokens=4000,
    summary_template=memory_template["summary_template"]
)
```

## 自定义提示模板

创建自定义提示模板的步骤：

1. 在适当的子目录中创建新模板文件（YAML或JSON格式）
2. 定义模板结构，包括必要的变量占位符
3. 在代码中加载并使用模板

提示模板设计原则：
- 明确指令
- 结构清晰
- 适当约束
- 包含示例（当适用时）

## 提示模板变量

常用变量包括：
- `${name}`: 角色名称
- `${background}`: 背景信息
- `${personality}`: 性格特征
- `${history}`: 对话历史
- `${task}`: 当前任务

可以根据需要定义其他自定义变量。