# MengLong Models (模型访问层)

这是 MengLong SDK 的核心访问层。它采用了 **Facade (外观) 模式** 和 **Strategy (策略) 模式**，旨在为用户提供一个统一、无缝且高性能的多模型访问入口。

## 核心特性

- **统一入口 (Smart Facade)**：无论是 OpenAI 还是 DeepSeek，你只需要通过 `Model` 类即可访问。
- **智能路由 (Dynamic Routing)**：支持在运行时通过参数指定 `model_id`，实现供应商的平滑切换。
- **按需加载 (On-demand Loading)**：适配器模块仅在被调用时动态加载，保持核心框架极简。
- **实例池化 (Provider Pooling)**：自动缓存已创建的模型客户端，提升高频调用性能。

## 快速上手

### 1. 初始化模型
你可以指定一个默认模型 ID（格式为 `provider/model`）：

```python
from menglong.models.model import Model

# 使用 OpenAI GPT-4 作为默认模型
model = Model(default_model_id="openai/gpt-4")
```

### 2. 同步聊天 (Chat)
```python
messages = [{"role": "user", "content": "你好，请介绍一下你自己"}]

# 使用默认模型
response = model.chat(messages)
print(response.text)

# 实时切换到 DeepSeek 进行对话
ds_response = model.chat(messages, model="deepseek/deepseek-chat")
print(ds_response.text)
```

### 3. 流式聊天 (Stream Chat)
```python
stream = model.stream_chat(messages)
for chunk in stream:
    if chunk.output.delta.text:
        print(chunk.output.delta.text, end="", flush=True)
```

### 4. 向量嵌入 (Embedding)
```python
texts = ["人工智能", "深度学习"]
embed_res = model.embed(texts, model="openai/text-embedding-3-small")
print(embed_res.embeddings[0]) # 获取第一个文本的向量
```

## 配置说明
模型层通过自动匹配 `.configs.toml` 中的 `provider` 名称来读取 API Key 和 Base URL。例如：

```toml
[providers.openai]
api_key = "sk-..."
base_url = "https://api.openai.com/v1"

[providers.deepseek]
api_key = "sk-..."
```

## 架构扩展
- **添加新平台**：只需在 `providers/` 目录下新增适配器并使用 `@ProviderRegistry.register` 注册，`Model` 层即可通过 `provider_name/xxx` 自动识别并调用。
