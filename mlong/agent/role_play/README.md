# 角色扮演（Role Play）模块

角色扮演模块提供了创建和管理具有特定角色的智能体的能力，支持单角色与多角色交互场景。

## 模块结构

- **role_play_agent.py**: 单角色扮演智能体，用于模拟特定角色与人类对话
- **two_role_play_agent.py**: 双角色扮演智能体，支持两个智能体角色之间的对话
- **yao_guang.py**: 耀光模式实现，支持更复杂的角色扮演场景

## 对话模式

### 单角色扮演（Single Role Play with Human）

单个智能体与人类的对话模拟，智能体扮演特定角色，具有专门的背景、个性和行为特征。

主要特点：
- 一问一答模式
- 角色扮演的连贯性
- 支持短期记忆和上下文理解

### 多角色扮演（Multi-Agent Role Play）

多个智能体角色之间的对话模拟，可以是两个角色的一对一对话，也可以是多个角色的群体讨论。

#### 双角色对话

双角色对话可以看作是特殊的对话模式，由两个角色之间互相交流组成：
- 主动方（active）：话题发起者
- 被动方（passive）：话题回答者

使用方式：
```python
init_two(agent_a, agent_c)  # agent_a 主动发起，agent_c 被动回应
```

#### 多人对话

多人对话被视为一种"讨论"模式，可以有不同的讨论规则：
- 自由讨论
- 主题讨论
- 有主持人的讨论

使用方式：
```python
init_multi(agent_a, agent_b, agent_c, agent_d)  # agent_a 作为主持人，其他为参与者
```

## 话题定义结构

角色扮演中的话题定义包含以下要素：

- **task background description**: 任务背景描述
- **role aim**: 角色的目标
- **notice**: 注意事项
- **end condition**: 结束条件

## 使用示例

```python
from mlong.model import Model
from mlong.agent.role_play.role_play_agent import RolePlayAgent

# 创建模型
model = Model()

# 定义角色信息
role_info = {
    "role": {
        "name": "李教授",
        "background": "一位资深的计算机科学教授，专注于人工智能研究20年",
        "personality": "严谨、耐心、善于解释复杂概念"
    },
    "role_system": "你是${name}，${background}。你的性格是${personality}。请以学术风格回应问题。"
}

# 创建角色扮演智能体
agent = RolePlayAgent(model=model, role_info=role_info)

# 与角色对话
response = agent.chat("请解释一下神经网络的工作原理。")
print(response)
```

## 高级用法

### 耀光模式（Yao Guang）

耀光模式是一种更复杂的角色扮演实现，支持更丰富的角色背景和交互逻辑，可以创建更真实、更生动的角色扮演体验。

```python
from mlong.agent.role_play.yao_guang import YaoGuangAgent

# 从配置文件创建耀光模式角色
agent = YaoGuangAgent.from_config("examples/example_configs/yaogunag_st.json")

# 与角色对话
response = agent.chat("你能告诉我你的生活是什么样的吗？")
print(response)
