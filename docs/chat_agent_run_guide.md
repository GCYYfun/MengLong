# ChatAgent.run() 自主任务执行功能

## 概述

已将 `AutonomousTaskExecutor` 的功能集成到 `ChatAgent` 的 `run()` 方法中，现在你可以直接调用 `agent.run(task)` 让 ChatAgent 自主执行任务直到完成。

## 核心功能

- **自主任务执行**: Agent 会自动分解任务、制定计划、选择工具并执行
- **进度跟踪**: 实时监控任务执行进度和状态
- **智能重试**: 遇到问题时自动寻找替代方案
- **结果验证**: 自动验证任务完成情况
- **详细日志**: 记录完整的执行过程和结果

## 使用方法

### 基本用法

```python
from menglong.agents.chat.chat_agent import ChatAgent, ChatMode

# 1. 创建 ChatAgent
agent = ChatAgent(
    mode=ChatMode.AUTO,
    system="你是一个专业的助手"
)

# 2. 注册工具
agent.register_global_tools()  # 注册所有全局工具

# 3. 执行任务
result = agent.run(
    task="请帮我研究人工智能在医疗领域的应用，并生成一份报告",
    max_iterations=10
)

# 4. 查看结果
print(f"任务状态: {result['status']}")
print(f"执行时间: {result['execution_time']:.2f}秒")
print(f"执行轮次: {result['iterations']}")
```

### 高级用法

```python
# 使用特定工具
agent.register_tools_from_functions(search_tool, analysis_tool, report_tool)

# 自定义系统提示
agent = ChatAgent(
    mode=ChatMode.AUTO,
    system="""你是一个专业的数据分析师，擅长：
- 数据收集和清理
- 统计分析和建模
- 报告生成和可视化"""
)

# 执行复杂任务
task = """
分析电商销售数据：
1. 收集相关市场数据
2. 进行趋势分析
3. 生成洞察报告
4. 提出改进建议
"""

result = agent.run(task=task, max_iterations=8)
```

## 返回结果

`agent.run()` 返回一个包含执行信息的字典：

```python
{
    "task_description": "原始任务描述",
    "status": "completed|incomplete",  # 任务状态
    "execution_time": 28.5,            # 执行时间（秒）
    "iterations": 5,                   # 实际执行轮次
    "max_iterations": 10,              # 最大轮次限制
    "execution_log": [...],            # 详细执行日志
    "success_rate": 1.0                # 成功率
}
```

## 工具注册方式

### 1. 注册全局工具

```python
# 注册所有用 @tool 装饰的全局工具
agent.register_global_tools()
```

### 2. 注册特定函数

```python
from your_tools import search_web, analyze_data, generate_report

agent.register_tools_from_functions(search_web, analyze_data, generate_report)
```

### 3. 从模块注册

```python
import my_tools_module

agent.register_tools_from_module(my_tools_module)
```

## 最佳实践

### 1. 任务描述要清晰

```python
# ✅ 好的任务描述
task = """
请完成市场调研报告：
1. 搜索人工智能市场的最新数据
2. 分析主要厂商的市场份额
3. 识别发展趋势和机会
4. 生成包含图表的报告
5. 保存报告文件
"""

# ❌ 模糊的任务描述
task = "帮我研究一下AI"
```

### 2. 合理设置迭代次数

```python
# 简单任务
result = agent.run(task="搜索并总结一个主题", max_iterations=3)

# 复杂任务
result = agent.run(task="完整的市场调研项目", max_iterations=10)
```

### 3. 为不同类型任务配置专门的Agent

```python
# 研究型Agent
research_agent = ChatAgent(
    mode=ChatMode.AUTO,
    system="你是专业的研究助手，擅长信息收集、分析和报告生成"
)

# 数据分析型Agent
analysis_agent = ChatAgent(
    mode=ChatMode.AUTO,
    system="你是数据科学专家，精通统计分析、建模和可视化"
)
```

## 示例场景

### 场景1: 市场调研

```python
agent = ChatAgent(mode=ChatMode.AUTO)
agent.register_global_tools()

task = "调研电动汽车市场，分析竞争格局，生成投资建议报告"
result = agent.run(task=task, max_iterations=8)
```

### 场景2: 数据分析

```python
agent = ChatAgent(
    mode=ChatMode.AUTO,
    system="你是数据分析专家"
)
agent.register_tools_from_functions(data_loader, analyzer, visualizer)

task = "分析销售数据，找出增长驱动因素，生成业务洞察"
result = agent.run(task=task, max_iterations=6)
```

### 场景3: 内容创作

```python
agent = ChatAgent(
    mode=ChatMode.AUTO,
    system="你是专业的内容创作者"
)
agent.register_tools_from_functions(research_tool, writer, editor)

task = "创作一篇关于区块链技术的技术白皮书"
result = agent.run(task=task, max_iterations=7)
```

## 错误处理

```python
try:
    result = agent.run(task=task, max_iterations=5)
    
    if result['status'] == 'completed':
        print("✅ 任务成功完成")
    else:
        print("⚠️ 任务未完全完成")
        print(f"完成进度: {result['success_rate']:.1%}")
        
except Exception as e:
    print(f"❌ 执行出错: {e}")
```

## 性能建议

1. **合理设置迭代次数**: 根据任务复杂度调整 `max_iterations`
2. **优化工具响应时间**: 确保工具函数执行效率
3. **使用适当的系统提示**: 帮助Agent更好地理解任务目标
4. **监控执行日志**: 通过 `execution_log` 分析和优化执行过程

## 注意事项

- Agent 会在 AUTO 模式下自动执行，确保已正确配置
- 工具调用可能产生费用，请监控 API 使用情况
- 复杂任务可能需要较长时间，建议合理设置超时
- 定期检查和更新工具函数以确保功能正常
