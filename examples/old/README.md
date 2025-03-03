# Examples 示例代码

本目录包含了朦胧框架的各种使用示例，帮助开发者快速上手和了解框架功能。

## 基础示例

- **example_client.py**: 基础客户端使用示例
- **example_client_stream_chat.py**: 流式聊天客户端示例
- **example_client_thinking.py**: 思考过程可视化示例
- **example_chat_man.py**: 手动聊天示例

## 角色扮演示例

- **example_roleplay_agent.py**: 单角色扮演智能体示例
- **example_roleplay_agent_stream.py**: 流式输出的角色扮演智能体示例
- **example_roleplay_agent_stream_client.py**: 使用客户端的流式角色扮演示例
- **example_roleplay_chat.py**: 角色扮演聊天示例

## 多角色交互示例

- **example_two_roleplay_agent.py**: 双角色交互示例
- **example_two_roleplay_agent_stream_client.py**: 使用客户端的流式双角色交互示例

## 高级角色扮演示例

- **example_yao_guang.py**: 耀光模式完整示例
- **example_yao_guang_simple.py**: 耀光模式简化示例

## 示例配置文件 (example_configs/)

配置文件目录包含了各种预定义的配置示例：

- **default_npc.yaml**: 默认NPC角色配置
- **linyuqiu.yaml**: 林语秋角色配置示例
- **two_npc.yaml**: 双角色NPC配置
- **two_with_mem.yaml**: 带记忆系统的双角色配置
- **yaogunag_st.json**: 耀光模式配置示例

## 运行示例

要运行任何示例，请确保已安装朦胧框架，然后使用Python执行示例脚本：

```bash
# 安装框架
pip install -e .

# 运行基础客户端示例
python examples/example_client.py

# 运行角色扮演示例
python examples/example_roleplay_agent.py
```

## 配置说明

大多数示例都支持通过配置文件或命令行参数来自定义行为。配置文件通常包含以下内容：

- 模型选择与配置
- 角色定义与个性设置
- 记忆系统配置
- 特定场景的参数

示例：

```yaml
# 配置文件示例 (examples/example_configs/default_npc.yaml)
role:
  name: "助手"
  background: "一位乐于助人的AI助手"
  personality: "友好、耐心、知识渊博"

memory:
  short_term: true
  working: false
  episodic: false
  
model:
  provider: "anthropic"
  model_name: "claude-3.5-sonnet"
  temperature: 0.7
```

请参考各个示例文件中的注释和文档字符串，了解更详细的使用说明。