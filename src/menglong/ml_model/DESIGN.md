# 统一模型API框架设计文档

## 1. 项目概述

本项目旨在创建一个统一的API框架，用于封装市面上各大厂商（如OpenAI、百度、阿里、腾讯等）的模型服务接口。通过这个框架，用户只需指定模型ID，系统就能自动实例化对应厂商的客户端，并返回统一格式的响应结果。

## 2. 核心设计目标

- **统一接口**：提供一致的API调用方式，屏蔽不同厂商API的差异
- **动态加载**：根据模型ID自动选择并实例化对应厂商的客户端
- **统一响应**：将不同厂商的响应格式转换为统一的格式
- **可扩展性**：易于添加新的模型厂商支持
- **错误处理**：统一的错误处理机制

## 3. 系统架构

### 3.1 整体架构

```
+------------------+
|      Model       |
+--------+---------+
         |
         v
+--------+---------+
|  UnifiedModelAPI  |
+--------+---------+
         |
         v
+--------+---------+
| ModelClientFactory|
+--------+---------+
         |
         v
+--------+---------+     +------------------+
|  ModelClientBase  |<----| Configuration    |
+--------+---------+     +------------------+
         |
         +----------------+----------------+
         |                |                |
+--------v------+ +-------v-------+ +------v--------+
| OpenAIAdapter | | BaiduAdapter  | | Other Adapters |
+---------------+ +---------------+ +---------------+
```

### 3.2 核心组件

#### 3.2.1 UnifiedModelAPI

作为框架的主入口，提供统一的API调用接口。

#### 3.2.2 ModelClientFactory

工厂类，负责根据模型ID创建对应的客户端实例。

#### 3.2.3 ModelClientBase

所有厂商适配器的基类，定义统一的接口方法。

#### 3.2.4 厂商适配器

针对各个厂商的具体实现，如OpenAIAdapter、BaiduAdapter等。

#### 3.2.5 配置管理

管理API密钥、服务地址等配置信息。

## 4. 详细设计

### 4.1 模型ID设计

为了简化用户使用体验，模型ID采用统一的标识符格式，无需显式指定厂商信息。框架内部维护模型映射表，自动处理厂商关联。

#### 4.1.1 模型ID格式

直接使用模型名称作为标识符，例如：

- `gpt-4o`
- `ernie-bot`
- `qwen-7b`

#### 4.1.2 模型映射表

框架支持两种模型映射方式：

1. **静态映射**：框架内部预定义的模型到厂商的映射关系

```python
MODEL_VENDOR_MAPPING = {
    'gpt-4': 'openai',
    'gpt-3.5-turbo': 'openai',
    'ernie-bot': 'baidu',
    'ernie-bot-4': 'baidu',
    'qwen-7b': 'aliyun',
    # 可扩展更多模型...
}
```

2. **动态映射**：通过调用各厂商API自动获取最新模型列表并生成映射表

```python
class ModelDiscovery:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.vendor_clients = {}
        self.model_mapping = {}
    
    def register_vendor(self, vendor_name, client):
        """注册厂商客户端用于获取模型列表"""
        self.vendor_clients[vendor_name] = client
    
    def discover_models(self):
        """从所有注册的厂商获取模型列表并更新映射表"""
        for vendor, client in self.vendor_clients.items():
            try:
                models = client.list_models()
                for model in models:
                    self.model_mapping[model['id']] = vendor
            except Exception as e:
                print(f"从{vendor}获取模型列表失败: {e}")
        
        return self.model_mapping
    
    def get_mapping(self):
        """获取当前的模型映射表"""
        return self.model_mapping
```

#### 4.1.3 自动厂商识别

框架根据模型ID自动查找对应的厂商信息：

```python
def get_vendor_by_model_id(model_id: str) -> str:
    """根据模型ID获取对应的厂商信息"""
    vendor = MODEL_VENDOR_MAPPING.get(model_id)
    if not vendor:
        raise ValueError(f"未知的模型ID: {model_id}")
    return vendor
```

### 4.2 统一接口定义

```python
class ModelClientBase:
    def chat_completion(self, messages, **kwargs):
        """聊天完成接口"""
        pass
        
    def completion(self, prompt, **kwargs):
        """文本完成接口"""
        pass
        
    def embedding(self, text, **kwargs):
        """文本嵌入接口"""
        pass
```

### 4.3 统一响应格式

```python
class ModelResponse:
    def __init__(self, content, raw_response=None, usage=None, model_id=None):
        self.content = content  # 主要内容
        self.raw_response = raw_response  # 原始响应
        self.usage = usage  # 使用统计
        self.model_id = model_id  # 使用的模型ID
```

### 4.4 错误处理

定义统一的异常类型：

```python
class ModelAPIError(Exception):
    def __init__(self, message, vendor=None, status_code=None, raw_error=None):
        self.message = message
        self.vendor = vendor
        self.status_code = status_code
        self.raw_error = raw_error
        super().__init__(self.message)
```

## 5. 使用示例

```python
from unified_model_api import UnifiedModelAPI

# 初始化API
api = UnifiedModelAPI()

# 配置API密钥
api.configure({
    "openai": {"api_key": "sk-xxx"},
    "baidu": {"api_key": "xxx", "secret_key": "xxx"}
})

# 使用GPT-4模型（框架自动识别为OpenAI）
response = api.chat_completion(
    model_id="gpt-4",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.content)

# 使用文心一言模型（框架自动识别为百度）
response = api.chat_completion(
    model_id="ernie-bot",
    messages=[
        {"role": "user", "content": "你好，请介绍一下自己"}
    ]
)

print(response.content)
```

## 6. 扩展性设计

### 6.1 添加新厂商支持

1. 创建新的适配器类，继承自ModelClientBase
2. 实现必要的接口方法
3. 在ModelClientFactory中注册新的适配器

### 6.2 支持新功能

1. 在ModelClientBase中定义新的接口方法
2. 在各个适配器中实现该方法

## 7. 后续规划

- 支持更多厂商：Google、Anthropic、Cohere等
- 添加更多功能：图像生成、语音识别等
- 性能优化：连接池、缓存机制等
- 监控与日志：调用统计、性能监控等
- 高级功能：模型路由、负载均衡等

## 8. 技术选型

- 编程语言：Python 3.8+
- 依赖管理：Poetry/Pip
- HTTP客户端：Requests/HTTPX
- 异步支持：asyncio/HTTPX
- 测试框架：Pytest

## 9. 项目结构

```
api_framework/
├── unified_model_api/
│   ├── __init__.py
│   ├── api.py              # 主API类
│   ├── factory.py          # 工厂类
│   ├── base.py             # 基类定义
│   ├── config.py           # 配置管理
│   ├── response.py         # 响应类定义
│   ├── errors.py           # 错误定义
│   └── providers/          # 供应商适配器目录
│       ├── __init__.py
│       ├── openai.py       # OpenAI供应商适配器
│       ├── baidu.py        # 百度供应商适配器
│       └── ...            # 其他供应商适配器

框架会自动扫描providers目录下的所有Python文件，每个文件代表一个供应商适配器。
通过动态加载这些文件，系统可以自动发现所有可用的供应商，无需手动注册。
每个供应商适配器需要实现以下功能：
1. 继承ModelClientBase基类
2. 提供get_supported_models()方法，返回该供应商支持的模型列表
3. 实现必要的接口方法（如chat_completion等）
├── tests/                  # 测试目录
├── examples/               # 示例代码
├── pyproject.toml          # 项目配置
└── README.md               # 项目说明
```

## 10. 总结

本项目通过工厂模式和适配器模式，实现了对各大厂商模型API的统一封装。用户只需通过模型ID指定所需模型，系统就能自动实例化对应的客户端并返回统一格式的结果，大大简化了多模型集成的复杂度。