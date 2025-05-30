# Model Interface 模型接口

## 模块概述

`model_interface`是一个统一的模型API工具，用于封装和管理各大厂商（如OpenAI、Anthropic、AWS等）的模型服务接口。用户只需指定模型ID，系统就能自动实例化对应厂商的客户端，并返回统一格式的响应结果。

## 核心组件

- **model.py**: 统一模型API的主入口类，负责模型实例化和请求处理
- **provider.py**: 提供商工厂类，负责创建和管理不同厂商的客户端
- **providers/**: 各厂商适配器实现目录
- **schema/**: 请求和响应的数据结构定义
- **utils/**: 工具类和辅助函数

## 使用示例

```python
from mlong.model_interface import Model

# 初始化模型接口
model = Model(
    model_id="gpt-4o",  # 可选，如不指定则使用配置文件中的默认值
    configs={
        "openai": {"api_key": "sk-xxx"},
        "aws": {"region_name":""xxx", aws_access_key_id": "xxx", "aws_secret_access_key": "xxx"}
    }
)

# 发送聊天请求
response = model.chat(
    messages=[
        {"role": "user", "content": "你好，请介绍一下自己"}
    ]
)

print(response.content)

# 切换模型
model.chat_model_id = "ernie-bot"
response = model.chat(
    messages=[
        {"role": "user", "content": "你好，请介绍一下自己"}
    ]
)
# or
response = model.chat(
    model_id="ernie-bot",
    messages=[
        {"role": "user", "content": "你好，请介绍一下自己"}
    ]
)

print(response.content)
```

## 扩展指南

### 添加新的模型提供商

1. 在`providers/`目录下创建新的提供商适配器文件
2. 实现必要的接口方法（如`chat`、`embed`等）
3. 在`model_registry.py`中注册新的模型映射

### 配置文件

默认配置文件位于项目根目录的`.configs.template`，包含各提供商的API密钥和配置信息。使用时需要将其复制为`.configs`并填入实际的配置值。

### 错误处理

框架提供统一的错误处理机制，所有API调用异常都会被转换为标准格式的错误响应，便于上层应用处理。

## 更多信息

- API文档请参考：[model_api.md](../../docs/model_api.md)