# @tool 装饰器自动参数生成指南

## 概述

我们的 `@tool` 装饰器现在支持完全自动从函数签名和 docstring 中生成复杂的参数格式，包括您要求的标准 JSON Schema 格式。

## 支持的自动生成方式

### 1. 完全自动生成（推荐）

只需使用 `@tool()` 装饰器，不传任何参数，系统会自动：
- 从类型注解推断参数类型
- 从 docstring 提取参数描述
- 从默认值确定必需参数
- 从 `Literal` 和 `Enum` 生成 `enum` 属性

```python
@tool()  # 不传任何参数，完全自动
def get_weather(
    location: str,
    unit: Literal["celsius", "fahrenheit"] = "celsius"
):
    """
    获取天气信息
    
    Args:
        location: The city and state, e.g. San Francisco, CA
        unit: The unit of temperature, either "celsius" or "fahrenheit"
    """
    pass
```

**生成的参数格式**：
```json
{
  "type": "object",
  "properties": {
    "location": {
      "type": "string",
      "description": "The city and state, e.g. San Francisco, CA"
    },
    "unit": {
      "type": "string",
      "description": "The unit of temperature, either \"celsius\" or \"fahrenheit\"",
      "enum": ["celsius", "fahrenheit"],
      "default": "celsius"
    }
  },
  "required": ["location"]
}
```

### 2. 支持的类型注解

#### 基础类型
- `str` → `"type": "string"`
- `int` → `"type": "integer"`
- `float` → `"type": "number"`
- `bool` → `"type": "boolean"`

#### 复杂类型
- `List[str]` → `"type": "array", "items": {"type": "string"}`
- `Dict[str, Any]` → `"type": "object"`
- `Optional[str]` → `"type": "string"` + 不在 required 中
- `Union[str, int]` → `"type": "string"` (取第一个类型)

#### 枚举类型
- `Literal["a", "b"]` → `"enum": ["a", "b"]`
- `MyEnum` → `"enum": [e.value for e in MyEnum]`

### 3. 枚举类自动生成

```python
from enum import Enum

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@tool()
def create_task(
    title: str,
    priority: Priority = Priority.MEDIUM
):
    """创建任务"""
    pass
```

**自动生成**：
```json
{
  "properties": {
    "priority": {
      "type": "string",
      "enum": ["low", "medium", "high"],
      "default": "medium"
    }
  }
}
```

### 4. 复杂示例

```python
@tool()
def search_database(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    sort_by: Literal["date", "relevance", "title"] = "relevance",
    limit: int = 10,
    include_metadata: bool = False
):
    """
    搜索数据库
    
    Args:
        query: 搜索关键词
        filters: 搜索过滤条件，支持任意键值对
        sort_by: 排序方式
        limit: 返回结果数量限制 (1-100)
        include_metadata: 是否包含元数据信息
    """
    pass
```

**自动生成完整的 JSON Schema**：
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "搜索关键词"
    },
    "filters": {
      "type": "object",
      "description": "搜索过滤条件，支持任意键值对",
      "default": null
    },
    "sort_by": {
      "type": "string",
      "description": "排序方式",
      "enum": ["date", "relevance", "title"],
      "default": "relevance"
    },
    "limit": {
      "type": "integer",
      "description": "返回结果数量限制 (1-100)",
      "default": 10
    },
    "include_metadata": {
      "type": "boolean",
      "description": "是否包含元数据信息",
      "default": false
    }
  },
  "required": ["query"]
}
```

## 对比手动定义

### 手动定义的优势
- 可以添加更多约束（`minLength`, `maxLength`, `minimum`, `maximum`）
- 完全控制参数结构
- 可以添加 `additionalProperties` 等高级属性

### 自动生成的优势
- 代码更简洁，减少重复
- 自动同步函数签名和参数描述
- 支持所有常用的参数类型和格式
- 从 docstring 自动提取描述，保持文档同步

## 最佳实践

1. **优先使用自动生成**：对于大多数工具，自动生成已经足够
2. **混合使用**：对于需要特殊约束的参数，可以手动定义
3. **详细的 docstring**：在 Args 部分为每个参数提供清晰的描述
4. **使用类型注解**：充分利用 Python 的类型系统
5. **使用 Literal 和 Enum**：为有限选项的参数使用枚举类型

## 示例运行

参考 `examples/complete_tool_format_demo.py` 查看完整的演示和测试用例，包括：
- 5 种不同的自动生成示例
- 与手动定义的对比
- 实际工具执行测试
- 复杂参数类型处理

运行演示：
```bash
cd /Users/own/Workspace/MengLong
python examples/complete_tool_format_demo.py
```
