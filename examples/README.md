# MengLong 示例程序

这个目录包含了 MengLong 项目的各种示例程序，展示了不同功能和使用方法。

## 安装依赖

在运行示例前，请确保已安装所需的依赖：

```bash
pip install -r requirements.txt
```

如果您尚未安装 mlong，请按照项目主目录的 README.md 指示进行安装。

## 配置文件

所有配置文件都存放在 `configs` 目录中。在运行需要配置的示例前，请确保配置文件已正确设置。

## 可用示例

### 基础聊天示例

- **demo_chat.py**: 基础聊天演示
- **demo_chat_stream.py**: 基础流式聊天演示

### 角色扮演和记忆

- **demo_fluctlight.py**: FluctLight 角色演示（带有记忆功能）
- **ui_fluctlight.py**: FluctLight 的 Streamlit 图形界面演示

### 代理和工作流

- **demo_agent_chat.py**: 基础代理聊天演示
- **demo_agent_chat_stream.py**: 流式代理聊天演示
- **demo_ata_chat.py**: ATA (Assistant-Tool-Agent) 聊天演示
- **demo_ata_chat_stream.py**: 流式 ATA 聊天演示
- **demo_workflow.py**: 工作流演示

### 用户界面示例

- **ui_ata_chat_stream.py**: ATA 流式聊天的 Streamlit 图形界面

### 检索增强生成 (RAG)

- **demo_basic_rag.py**: 基础 RAG 演示
- **demo_embed.py**: 嵌入演示
- **demo_vector_db.py**: 向量数据库演示

### 其他高级示例

- **demo_ftf_chat.py**: FTF (Function-Tool-Function) 聊天演示
- **demo_world.py**: 世界模拟演示

## 运行示例

要运行任何示例，请使用 Python 直接执行：

```bash
python examples/[示例文件名]
```

对于 Streamlit 界面，运行：

```bash
streamlit run examples/[ui_示例文件名]
```

例如：

```bash
# 运行 FluctLight 命令行演示
python examples/demo_fluctlight.py

# 运行 FluctLight Streamlit 界面演示
streamlit run examples/ui_fluctlight.py
```

## 注意事项

- 某些演示可能需要特定的模型配置或API密钥
- 对于带有记忆功能的示例，记忆文件会存储在 `configs` 目录中
- 如需自定义配置，请修改 `configs` 目录中的相应文件
