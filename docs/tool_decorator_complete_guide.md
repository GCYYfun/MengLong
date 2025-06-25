# @tool 装饰器完整使用指南

## 回答您的问题：为什么是 @tool() 而不是 @tool？

我们的装饰器现在**同时支持两种形式**：

### 1. `@tool` (不带括号) - 直接装饰器
```python
@tool  # 简洁形式
def my_function(param: str):
    pass
```

### 2. `@tool()` (带括号) - 装饰器工厂
```python
@tool()  # 可以传参数的形式
def my_function(param: str):
    pass

@tool(description="自定义描述")  # 带参数
def my_function(param: str):
    pass
```

## 技术原理

**Python 装饰器的两种实现机制：**

1. **直接装饰器** (`@tool`)：
   ```python
   # 等价于：my_function = tool(my_function)
   @tool
   def my_function():
       pass
   ```

2. **装饰器工厂** (`@tool()`)：
   ```python
   # 等价于：decorator = tool(); my_function = decorator(my_function)
   @tool()
   def my_function():
       pass
   ```

## 我们的智能实现

我们通过检查第一个参数的类型来智能识别：

```python
def tool(func_or_name=None, *, description=None, parameters=None):
    def decorator(func):
        # 装饰逻辑
        return func
    
    # 如果第一个参数是函数，直接装饰
    if callable(func_or_name):
        return decorator(func_or_name)
    
    # 否则返回装饰器函数
    return decorator
```

## 完整功能支持

### ✅ 无 docstring 也能正常工作

即使没有 docstring，我们的系统也能：
- ✅ 正确推断参数类型
- ✅ 生成智能参数描述
- ✅ 识别枚举值和默认值
- ✅ 创建完整的 JSON Schema

**示例：**
```python
@tool  # 没有 docstring
def calculator(a: int, b: int, operation: Literal["add", "subtract"] = "add"):
    return a + b if operation == "add" else a - b
```

**自动生成的参数规范：**
```json
{
  "type": "object",
  "properties": {
    "a": {
      "type": "integer",
      "description": "整数值"
    },
    "b": {
      "type": "integer", 
      "description": "整数值"
    },
    "operation": {
      "type": "string",
      "enum": ["add", "subtract"],
      "default": "add",
      "description": "字符串值，可选：add, subtract，默认：add"
    }
  },
  "required": ["a", "b"]
}
```

### 🧠 智能描述生成

当没有 docstring 时，系统会基于参数名和类型生成智能描述：

| 参数名模式 | 自动生成的描述 |
|-----------|---------------|
| `query`, `search`, `keyword` | "搜索关键词" |
| `email`, `mail` | "邮箱地址" |
| `text`, `content`, `body` | "文本内容" |
| `count`, `num`, `number` | "数量或计数" |
| `limit`, `max`, `maximum` | "数量限制" |
| `name`, `title`, `subject` | "名称或标题" |
| `url`, `link`, `address` | "URL地址或链接" |
| 其他 | 基于类型生成基础描述 |

### 📋 所有支持的用法

```python
# 1. 最简单的用法
@tool
def simple_func(param: str):
    pass

# 2. 带括号但不传参
@tool()
def auto_func(param: str):
    pass

# 3. 自定义描述
@tool(description="自定义工具描述")
def custom_desc_func(param: str):
    pass

# 4. 自定义名称和描述
@tool("custom_name", description="自定义工具")
def some_func(param: str):
    pass

# 5. 手动指定参数规范
@tool(parameters={
    "type": "object",
    "properties": {
        "param": {"type": "string", "description": "手动定义"}
    },
    "required": ["param"]
})
def manual_params_func(param: str):
    pass
```

## 使用建议

1. **简单情况优选 `@tool`**：代码更简洁
2. **需要自定义时用 `@tool(...)`**：更灵活
3. **写 docstring 获得最佳效果**：参数描述更准确
4. **充分利用类型注解**：自动生成更精确的类型信息

## 总结

- ✅ **两种形式都支持**：`@tool` 和 `@tool()`
- ✅ **无 docstring 也能工作**：智能生成参数描述
- ✅ **完全兼容您的目标格式**：生成标准 JSON Schema
- ✅ **智能类型推断**：支持所有常用 Python 类型
- ✅ **向后兼容**：不会破坏现有代码

现在您可以选择最舒适的方式使用我们的工具装饰器！
