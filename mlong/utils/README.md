# Utils 工具函数模块

utils 模块提供了框架中使用的各种通用工具函数，为其他模块提供基础功能支持。

## 模块结构

- **__init__.py**: 工具函数模块初始化
- **format.py**: 格式化相关工具函数
- **util.py**: 通用工具函数

## 主要功能

### 格式化工具 (format.py)

格式化工具提供了各种数据转换和格式化功能：
- 文本格式化
- 数据结构转换
- 输出美化
- 模板渲染

这些工具函数使各个模块能够以一致的方式处理和展示数据。

### 通用工具函数 (util.py)

通用工具函数提供了各种辅助功能：
- 文件操作
- 字符串处理
- 配置管理
- 日志记录
- 错误处理

这些功能为框架的其他组件提供了基础支持。

## 使用示例

### 格式化工具

```python
from mlong.utils.format import format_chat_history

# 格式化聊天历史
chat_history = [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮助你的？"},
    {"role": "user", "content": "请推荐一本书"}
]

formatted_history = format_chat_history(chat_history)
print(formatted_history)
```

### 通用工具函数

```python
from mlong.utils.util import load_config, setup_logger

# 加载配置文件
config = load_config("config.yaml")

# 设置日志记录器
logger = setup_logger("mlong", log_level="INFO")
logger.info("MengLong框架初始化完成")
```

## 扩展工具函数

要添加新的工具函数：
1. 确定函数应该放在哪个文件中（format.py或util.py，或创建新文件）
2. 实现函数并添加详细文档字符串
3. 在适当的地方导入和使用新函数

工具函数设计原则：
- 函数应当专注于单一功能
- 提供清晰的参数和返回值文档
- 包含适当的错误处理
- 避免副作用（除非明确说明）
- 保持无状态，便于测试和维护