# MengLong Agent SDK

这是一个用于开发 LLM Agent 的Python SDK库，旨在为开发人员提供简单易用的接口来构建智能代理应用。

## 安装方法

使用 uv 进行安装:

```bash
uv add git+https://github.com/gcyyfun/menglong.git
```


## 快速开始

以下是一个简单的示例，演示如何使用 MengLong Agent SDK:

```python
from menglong.agents import Agent

# 创建一个基础代理
agent = Agent(name="基础代理")
print(agent.run("你好，MengLong!"))
```



## 项目结构

```
menglong/
├── __init__.py        # 包的主入口
├── models/            # 模型层 - 统一AI厂商接口
├── components/        # 组件层 - 各种可复用组件
├── agents/            # 代理层 - 各种Agent实现
├── monitor/           # 监控层 - 全面监控能力
└── utils/             # 工具层 - 日志、工具等
```

