# Providers 模型提供商模块

providers 模块负责集成和管理不同的大语言模型提供商，提供统一的接口，使框架能够与多种模型服务进行交互。

## 模块结构

- **__init__.py**: 提供商模块初始化
- **aws_provider.py**: AWS 模型提供商的实现

## 支持的提供商

### AWS Provider (aws_provider.py)

AWS 提供商支持通过 AWS Bedrock 服务调用多种大语言模型：

- Claude 3.5
- Claude 3.7
- Nova Pro
- 其他 AWS Bedrock 支持的模型

## 提供商接口

所有提供商都实现了以下核心接口：

- **初始化**: 设置API密钥、端点和配置
- **请求格式化**: 将统一的请求格式转换为特定提供商的格式
- **响应解析**: 将提供商的响应转换为统一格式
- **错误处理**: 处理API调用中的各种错误和异常

## 使用示例

```python
from mlong.providers.aws_provider import AWSProvider

# 创建AWS提供商实例
provider = AWSProvider(
    region_name="us-west-2",
    credentials={
        "aws_access_key_id": "YOUR_ACCESS_KEY",
        "aws_secret_access_key": "YOUR_SECRET_KEY"
    }
)

# 准备请求参数
request_params = {
    "messages": [
        {"role": "user", "content": "请介绍一下深度学习"}
    ],
    "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "temperature": 0.7,
    "max_tokens": 1000
}

# 调用模型
response = provider.generate(request_params)
print(response["content"])
```

## 添加新提供商

要添加新的模型提供商：

1. 创建新的提供商文件，例如 `openai_provider.py`
2. 实现必要的接口方法
3. 在 `__init__.py` 中注册新提供商
4. 更新模型配置以支持新提供商的模型

提供商实现需要处理：
- 身份验证
- 请求格式转换
- 响应解析
- 错误处理
- 特定于提供商的参数管理