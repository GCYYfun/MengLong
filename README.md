# MengLong (朦胧)

## Introduction

《朦胧》是一个基于大语言模型(LLM)的智能体(agent)开发框架，用于支持各类agent应用的快速开发与部署。

朦胧提供了一套完整的智能体开发工具，包括模型集成、智能体抽象、记忆系统、对话管理、多角色扮演等功能。框架设计灵活，可以轻松适应不同类型的LLM应用场景。

名字是我听歌时，有了这个想法，刚好唱到这两个字，觉得很有意境，就用了这个名字。

## Features

- **多模型支持**: 集成多种LLM模型，包括OpenAI GPT-4、Anthropic Claude 3.5/3.7等
- **角色扮演系统**: 支持单角色与多角色对话，可构建复杂的角色间互动场景
- **记忆系统**: 支持短期记忆、工作记忆和情节记忆，使智能体具有上下文感知能力
- **工具调用**: 支持Python解释器、向量数据库等工具的集成
- **流式响应**: 支持流式输出，提升用户体验
- **可扩展架构**: 易于添加新模型提供商、新工具和新功能

## Getting Started

### Installation

```bash
# 从源码安装
git clone https://github.com/GCYYfun/MengLong.git
cd MengLong
pip install -e .

# 或者直接通过pip安装（一旦发布到PyPI）
# pip install mlong
```

### Quick Start

```python
from mlong.model import Model
from mlong.agent.role_play.role_play_agent import RolePlayAgent

# 1. 创建模型
model = Model()  # 默认使用Claude 3.7

# 2. 定义角色信息
role_info = {
    "role": {
        "name": "小明",
        "background": "一个热情友好的大学生，喜欢音乐和旅行",
        "personality": "开朗、乐观、友善"
    },
    "role_system": "你是${name}，${background}。你的性格是${personality}。请以第一人称回复用户问题。"
}

# 3. 创建角色扮演智能体
agent = RolePlayAgent(model=model, role_info=role_info)

# 4. 与智能体对话
response = agent.chat("你好！请做个自我介绍吧。")
print(response)
```

### 流式响应示例

```python
# 流式输出示例
for chunk in agent.chat_stream("你能给我讲个故事吗？"):
    print(chunk, end="", flush=True)
```

## Architecture

朦胧框架由以下核心组件构成:

- **Model**: 模型抽象层，统一管理不同的LLM模型接口
- **Provider**: 提供商适配层，支持OpenAI、Anthropic、AWS等不同提供商的API
- **Agent**: 智能体抽象，包括基础Agent和特定场景的实现(如RolePlayAgent)
- **Memory**: 记忆系统，支持短期、工作和情节记忆
- **Tools**: 工具集成，扩展智能体的能力
- **Types**: 类型定义，确保接口一致性
- **Utils**: 工具函数，提供通用功能

## Directory Structure

```
mlong/
├── __init__.py       # 包初始化
├── model.py          # 模型抽象层
├── provider.py       # 模型提供商管理
├── agent/            # 智能体模块
│   ├── agent.py      # 基础智能体类
│   ├── code_agent.py # 代码智能体实现
│   └── role_play/    # 角色扮演相关智能体
├── memory/           # 记忆系统
│   ├── short_term_memory.py
│   ├── working_memory.py
│   └── episodic_memory.py
├── prompts/          # 提示模板
│   ├── code/         # 代码相关提示
│   └── role_play/    # 角色扮演提示
├── providers/        # 模型提供商实现
│   ├── __init__.py
│   └── aws_provider.py
├── retrieval/        # 检索相关功能
│   ├── search/       # 搜索功能
│   └── vector/       # 向量检索
├── tools/            # 工具集成
│   ├── python_interpreter.py
│   └── vector_database.py
├── types/            # 类型定义
│   ├── type_chat.py
│   └── type_model.py
└── utils/            # 工具函数
    ├── format.py
    └── util.py
```

## Usage Examples

### 角色扮演

```python
# 查看examples目录中的示例脚本
# - example_roleplay_agent.py: 单角色扮演示例
# - example_two_roleplay_agent.py: 双角色交互示例
# - example_yao_guang.py: 更复杂的角色扮演应用
```

### 记忆系统

```python
# 集成记忆系统的示例可以参考
# - examples/example_configs/two_with_mem.yaml
```

## 示例配置

框架支持通过YAML或JSON配置文件定义智能体行为：

```yaml
# 角色扮演配置示例
role:
  name: "林语秋"
  background: "一位知识渊博的大学教授，专注于人工智能和哲学交叉领域研究"
  personality: "温和、思考深入、善于用类比解释复杂概念"

memory:
  short_term: true
  working: true
  episodic: false
```

更多示例配置可以在`examples/example_configs/`目录下找到。

## Contributing

欢迎贡献代码、提交问题或建议！

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交你的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启一个 Pull Request

## License

MIT License

Copyright (c) 2023-2024 MengLong Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

