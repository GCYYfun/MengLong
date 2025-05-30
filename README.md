# MengLong Agent SDK

这是一个用于创建和管理智能代理(Agent)的Python SDK库，旨在为开发人员提供简单易用的接口来构建智能代理应用。

## 功能特点

- 简单易用的代理创建和管理接口
- 灵活的代理类型扩展机制
- 完整的类型注解支持

## 安装方法

使用 uv 进行安装:

```bash
uv pip install menglong
```

或者从源代码安装:

```bash
git clone https://github.com/username/menglong.git
cd menglong
uv pip install -e .
```

## 快速开始

以下是一个简单的示例，演示如何使用 MengLong Agent SDK:

```python
import menglong
from menglong.agents import Agent

# 打印欢迎信息
print(menglong.hello())

# 创建一个基础代理
agent = Agent(name="我的第一个代理")
print(agent.run())
```

## 使用工厂方法创建代理

```python
from menglong.agents.factory import create_agent

# 使用工厂方法创建代理
agent = create_agent(agent_type="basic", name="工厂创建的代理")
print(agent.run())
```

## 项目结构

```
menglong/
├── __init__.py        # 包的主入口
├── core.py           # 核心功能实现
└── agents/           # 代理相关模块
    ├── __init__.py   # 包含基本代理类
    └── factory.py    # 代理工厂
```

## 开发指南

1. 克隆代码库
2. 安装开发依赖: `uv pip install -e ".[dev]"`
3. 运行测试: `pytest`

## 许可证

本项目采用 MIT 许可证。
