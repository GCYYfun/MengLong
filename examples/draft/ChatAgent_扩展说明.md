# ChatAgent 扩展功能说明

## 概述

本次对 `ChatAgent` 类进行了重大扩展，新增了 **workflow 模式** 和 **auto 模式**，使其从简单的聊天代理升级为功能强大的多模式智能助手。

## 🆕 新增功能

### 1. 三种聊天模式

#### **Normal Mode (普通模式)**
- 传统的对话模式
- 基本的用户-助手对话交互
- 适用于简单的问答场景

#### **Auto Mode (自动模式)**
- 支持工具调用功能
- 自动识别用户需求并调用相应工具
- 支持多轮工具调用
- 适用于需要外部功能辅助的复杂任务

#### **Workflow Mode (工作流模式)**
- 支持多步骤任务处理
- 可定义复杂的工作流程
- 支持条件执行和状态管理
- 适用于结构化的多阶段任务

### 2. 工具系统

#### **工具注册**
```python
agent.register_tool(
    name="get_weather",
    func=weather_function,
    description="获取天气信息",
    parameters={
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "城市名称"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
        },
        "required": ["location"]
    }
)
```

#### **工具调用**
- 自动格式化工具定义
- 智能参数解析
- 错误处理和结果返回

### 3. 工作流系统

#### **步骤定义**
```python
def analysis_step(input_msg, context):
    return "分析用户需求完成"

agent.add_workflow_step("需求分析", analysis_step)
```

#### **条件执行**
```python
def condition_check():
    return some_condition

agent.add_workflow_step("条件步骤", action_func, condition_check)
```

#### **状态管理**
- 实时跟踪工作流执行状态
- 支持步骤重置和状态查询
- 完整的执行历史记录

### 4. 异步支持

#### **异步接口**
```python
# 异步聊天
response = await agent.chat_async(message)

# 异步工作流步骤
async def async_step(input_msg, context):
    await asyncio.sleep(1)  # 模拟异步操作
    return "异步处理完成"
```

#### **任务调度**
- 集成了 `AsyncTaskScheduler`
- 支持并发任务执行
- 任务状态监控和管理

## 📝 使用示例

### 基本用法

```python
from src.menglong.agents.chat.chat_agent import ChatAgent, ChatMode

# 创建不同模式的Agent
normal_agent = ChatAgent(mode=ChatMode.NORMAL)
auto_agent = ChatAgent(mode=ChatMode.AUTO)
workflow_agent = ChatAgent(mode=ChatMode.WORKFLOW)
```

### 工具使用示例

```python
# 创建自动模式Agent
agent = ChatAgent(mode=ChatMode.AUTO)

# 注册天气工具
def get_weather(location: str, unit: str = "celsius"):
    return {"location": location, "temperature": 22, "condition": "晴天"}

agent.register_tool(
    name="get_weather",
    func=get_weather,
    description="查询天气信息",
    parameters={
        "type": "object",
        "properties": {
            "location": {"type": "string"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
        },
        "required": ["location"]
    }
)

# 用户查询天气，Agent会自动调用工具
response = agent.chat("北京今天天气怎么样？")
```

### 工作流使用示例

```python
# 创建工作流模式Agent
agent = ChatAgent(mode=ChatMode.WORKFLOW)

# 定义工作流步骤
def step1_analyze(input_msg, context):
    return f"分析需求: {input_msg}"

def step2_process(input_msg, context):
    return "处理任务中..."

def step3_respond(input_msg, context):
    return "生成最终回复"

# 添加工作流步骤
agent.add_workflow_step("分析", step1_analyze)
agent.add_workflow_step("处理", step2_process)
agent.add_workflow_step("回复", step3_respond)

# 执行工作流
response = agent.chat("请帮我分析市场趋势")

# 查看工作流状态
status = agent.get_workflow_status()
print(status)
```

### 异步工作流示例

```python
import asyncio

# 定义异步步骤
async def async_analysis(input_msg, context):
    await asyncio.sleep(2)  # 模拟耗时分析
    return "深度分析完成"

async def async_processing(input_msg, context):
    await asyncio.sleep(3)  # 模拟数据处理
    return "数据处理完成"

# 添加异步步骤
agent.add_workflow_step("异步分析", async_analysis)
agent.add_workflow_step("异步处理", async_processing)

# 异步执行
async def main():
    response = await agent.chat_async("复杂任务处理")
    print(response)

asyncio.run(main())
```

## 🏗️ 架构设计

### 核心类结构

```
ChatAgent
├── ChatMode (枚举)
│   ├── NORMAL
│   ├── AUTO
│   └── WORKFLOW
├── WorkflowStep (工作流步骤)
├── 工具管理
│   ├── register_tool()
│   ├── _format_tools_for_model()
│   └── _execute_tool_call()
├── 工作流管理
│   ├── add_workflow_step()
│   ├── get_workflow_status()
│   └── reset_workflow()
└── 聊天接口
    ├── chat()
    ├── chat_async()
    └── chat_stream()
```

### 模式处理流程

```
用户输入
    ↓
模式判断
    ├── Normal → _normal_chat()
    ├── Auto → _auto_chat() → 工具调用
    └── Workflow → _workflow_chat() → 步骤执行
    ↓
响应生成
    ↓
用户输出
```

## 📊 功能对比

| 功能 | Normal Mode | Auto Mode | Workflow Mode |
|------|-------------|-----------|---------------|
| 基础对话 | ✅ | ✅ | ✅ |
| 工具调用 | ❌ | ✅ | ✅ |
| 多步骤处理 | ❌ | ❌ | ✅ |
| 状态管理 | 基础 | 基础 | 完整 |
| 异步支持 | ✅ | ✅ | ✅ |
| 条件执行 | ❌ | ❌ | ✅ |
| 流式聊天 | ✅ | ✅ | ✅ |

## 🧪 测试验证

提供了三个演示文件来验证功能：

1. **chat_agent_simple_demo.py** - 简化演示，展示基本用法
2. **chat_agent_demo.py** - 完整演示，包含实际模型调用
3. **chat_agent_feature_test.py** - 功能验证，不依赖模型调用

### 运行测试

```bash
# 功能验证（推荐）
python examples/demo/chat_agent_feature_test.py

# 简化演示
python examples/demo/chat_agent_simple_demo.py

# 完整演示（需要配置模型）
python examples/demo/chat_agent_demo.py
```

## 🔧 API 参考

### 主要方法

#### 初始化
```python
ChatAgent(model_id=None, system=None, mode=ChatMode.NORMAL)
```

#### 工具管理
```python
# 注册工具
register_tool(name, func, description, parameters)

# 执行工具调用
_execute_tool_call(tool_name, arguments)

# 格式化工具
_format_tools_for_model()
```

#### 工作流管理
```python
# 添加步骤
add_workflow_step(name, action, condition=None)

# 查看状态
get_workflow_status()

# 重置工作流
reset_workflow()
```

#### 聊天接口
```python
# 同步聊天
chat(input_messages, **kwargs)

# 异步聊天
async chat_async(input_messages, **kwargs)

# 流式聊天
chat_stream(input_messages, **kwargs)
```

## 🚀 扩展性

### 自定义工具
用户可以轻松注册自定义工具函数，扩展Agent的能力范围。

### 复杂工作流
支持复杂的多分支、条件执行的工作流定义。

### 异步集成
完整的异步支持，可与现有异步框架无缝集成。

### 流式处理
为流式聊天和实时响应提供了接口基础。

## 📝 注意事项

1. **模型兼容性**：Auto模式需要模型支持工具调用功能
2. **异步处理**：异步工作流需要合适的事件循环环境
3. **错误处理**：工具调用和工作流执行都包含了完整的错误处理
4. **状态管理**：工作流状态会持久化，需要主动重置

## 🔄 版本更新

### v2.0 (当前版本)
- ✅ 新增 Auto 模式和 Workflow 模式
- ✅ 完整的工具注册和调用系统
- ✅ 多步骤工作流管理
- ✅ 异步任务支持
- ✅ 状态管理和条件执行
- ✅ 流式聊天接口

### v1.0 (原版本)
- ✅ 基本的 Normal 模式聊天功能

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进 ChatAgent 的功能！

---

**ChatAgent v2.0 - 让AI助手更智能、更灵活、更强大！** 🚀
