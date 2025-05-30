# Memory 记忆系统

记忆系统是朦胧框架中使智能体具备上下文理解能力的核心组件，包括多种记忆类型和管理机制。

## 模块结构

- **__init__.py**: 记忆系统初始化
- **short_term_memory.py**: 短期记忆实现
- **working_memory.py**: 工作记忆实现
- **episodic_memory.py**: 情节记忆实现

## 记忆类型

### 短期记忆 (Short-Term Memory)

短期记忆用于存储近期的对话历史，帮助智能体理解当前对话的上下文。

主要特点：
- 容量有限，通常保存最近的对话轮次
- 自动管理，超出容量时会自动删除最旧的记忆
- 高访问频率，在每次对话中都会被参考

### 工作记忆 (Working Memory)

工作记忆是智能体处理当前任务的临时工作空间，用于存储和处理当前任务相关的信息。

主要特点：
- 相对短期记忆更加结构化
- 可以存储关键信息、任务进展等
- 任务完成后可能会被清空或部分保留

### 情节记忆 (Episodic Memory)

情节记忆存储智能体的长期经验，可以让智能体回忆过去的交互并从中学习。

主要特点：
- 长期存储，可以跨会话保持
- 结构化存储，便于检索
- 可用于构建智能体的连续性体验

## 记忆内部结构

每种记忆类型都包含以下核心组件：
- 存储机制：如何存储和组织记忆内容
- 检索机制：如何访问和查询记忆
- 更新策略：如何添加新记忆和管理旧记忆

## 使用示例

### 短期记忆

```python
from mlong.memory.short_term_memory import ShortTermMemory

# 创建短期记忆
memory = ShortTermMemory(max_tokens=4000)

# 添加消息到记忆
memory.add_message({"role": "user", "content": "你好，请介绍自己。"})
memory.add_message({"role": "assistant", "content": "我是一个AI助手，很高兴为你服务。"})

# 获取记忆中的消息
messages = memory.get_messages()
print(messages)
```

### 工作记忆

```python
from mlong.memory.working_memory import WorkingMemory

# 创建工作记忆
memory = WorkingMemory()

# 存储信息
memory.store("user_preference", "喜欢科幻小说")
memory.store("current_topic", "人工智能")

# 检索信息
preference = memory.retrieve("user_preference")
print(preference)  # 输出: 喜欢科幻小说
```

### 集成到智能体

```python
from mlong.model import Model
from mlong.agent.role_play.role_play_agent import RolePlayAgent
from mlong.memory.short_term_memory import ShortTermMemory

# 创建模型和记忆
model = Model()
memory = ShortTermMemory(max_tokens=4000)

# 创建带有记忆的角色扮演智能体
agent = RolePlayAgent(
    model=model,
    role_info={"role": {"name": "助手"}},
    memory=memory
)

# 对话会自动使用记忆系统
response1 = agent.chat("我的名字叫张三。")
response2 = agent.chat("你还记得我的名字吗？")  # 能够回答"张三"
```

## 高级特性

- **记忆检索优化**: 支持基于相关性的记忆检索
- **记忆压缩**: 长对话历史的自动摘要和压缩
- **记忆持久化**: 支持将记忆保存到磁盘并在需要时加载