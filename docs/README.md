# MengLong Tool Call 文档集

这是 MengLong 框架工具调用功能的完整文档集，包含了详细的使用指南、技术规范和API参考。

## 📚 文档目录

### 1. [工具调用完整指南](./tool_call_documentation.md)
**适合对象**: 所有开发者
**内容概述**:
- 工具调用基础概念和流程
- 不同AI厂商工具格式对比（OpenAI、AWS、Anthropic、DeepSeek）
- 最佳实践和性能优化建议
- 常见问题故障排除

**核心内容**:
- ✅ 工具调用原理解析
- ✅ 厂商格式差异对比表
- ✅ 完整使用示例
- ✅ 错误处理和调试技巧

### 2. [Schema 规范文档](./schema_specification.md)
**适合对象**: 架构师、高级开发者
**内容概述**:
- MengLong 框架所有数据模型的完整规范
- 请求/响应模型详细说明
- 类型安全和数据验证机制
- 转换器设计模式

**核心内容**:
- ✅ 消息模型 (SystemMessage, UserMessage, AssistantMessage, ToolMessage)
- ✅ 响应模型 (ChatResponse, Content, ToolDesc, Usage)
- ✅ 流式响应和嵌入模型
- ✅ 转换器接口规范

### 3. [API 参考文档](./tool_call_api_reference.md)
**适合对象**: 实际编程的开发者
**内容概述**:
- `tool_call.py` 演示代码的详细API说明
- 所有函数签名和参数说明
- 完整的代码示例和使用场景
- 自定义工具开发指南

**核心内容**:
- ✅ 函数级别的详细说明
- ✅ 参数类型和返回值规范
- ✅ 错误处理实现
- ✅ 自定义工具开发模板

## 🚀 快速开始

### 1. 基础用法
```python
from menglong.ml_model import Model
from menglong.ml_model.schema.ml_request import SystemMessage, UserMessage

# 初始化模型
model = Model(model_id="gpt-4o")

# 定义工具
weather_tool = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "获取天气信息",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "城市名称"}
            },
            "required": ["location"]
        }
    }
}

# 发送请求
messages = [
    SystemMessage(content="你是天气助手"),
    UserMessage(content="北京今天天气怎么样？")
]

response = model.chat(
    messages=messages,
    tools=[weather_tool],
    tool_choice="auto"
)
```

### 2. 运行完整演示
```bash
cd examples/demo
python tool_call.py
```

## 📖 阅读建议

### 对于新手开发者
1. 先阅读 [工具调用完整指南](./tool_call_documentation.md) 的前半部分了解基础概念
2. 运行 `tool_call.py` 演示，观察输出结果
3. 参考 [API 参考文档](./tool_call_api_reference.md) 理解代码实现
4. 回到指南查看最佳实践部分

### 对于有经验的开发者
1. 直接查看 [Schema 规范文档](./schema_specification.md) 了解数据结构
2. 阅读 [工具调用完整指南](./tool_call_documentation.md) 的厂商对比部分
3. 参考 [API 参考文档](./tool_call_api_reference.md) 的自定义工具部分
4. 根据需要实现特定厂商的集成

### 对于架构师和技术负责人
1. 重点阅读 [Schema 规范文档](./schema_specification.md) 了解整体设计
2. 查看 [工具调用完整指南](./tool_call_documentation.md) 的架构设计部分
3. 评估不同厂商的技术选型建议

## 🔧 技术特性

### 支持的AI厂商
- **OpenAI**: GPT-4o, GPT-4, GPT-3.5-turbo
- **DeepSeek**: DeepSeek-Chat, DeepSeek-Coder
- **Anthropic**: Claude-3.5-Sonnet (通过 AWS Bedrock)
- **AWS Bedrock**: 多种模型支持

### 核心功能
- ✅ 统一的工具调用接口
- ✅ 自动格式转换
- ✅ 类型安全的数据模型
- ✅ 完整的错误处理
- ✅ 流式响应支持
- ✅ 丰富的日志记录

### 开发者友好特性
- ✅ 详细的类型注解
- ✅ 完整的文档说明
- ✅ 丰富的示例代码
- ✅ 单元测试覆盖
- ✅ 性能监控支持

## 📋 厂商格式快速对比

| 特性 | OpenAI | AWS Bedrock | Anthropic | DeepSeek |
|------|--------|-------------|-----------|----------|
| 顶层结构 | `type: "function"` | `toolSpec` | 扁平结构 | 兼容OpenAI |
| 参数位置 | `function.parameters` | `inputSchema.json` | `input_schema` | `function.parameters` |
| 工具选择 | `tool_choice: "auto"` | `tool_choice: {"type": "any"}` | 自动 | `tool_choice: "auto"` |
| 复杂度 | 中等 | 高 | 低 | 中等 |
| 兼容性 | 广泛 | AWS生态 | Claude专用 | OpenAI兼容 |

## 🛠️ 开发环境设置

### 1. 安装依赖
```bash
# 使用 pip
pip install menglong

# 或使用 poetry/uv (推荐)
uv add menglong
```

### 2. 配置环境变量
```bash
# OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# DeepSeek
export DEEPSEEK_API_KEY="your-deepseek-api-key"

# AWS (用于 Anthropic)
export AWS_ACCESS_KEY_ID="your-aws-access-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### 3. 验证安装
```python
python -c "from menglong.ml_model import Model; print('安装成功!')"
```

## 📝 示例代码库

### 基础示例
- **简单对话**: [examples/demo/chat.py](../examples/demo/chat.py)
- **工具调用**: [examples/demo/tool_call.py](../examples/demo/tool_call.py)
- **流式响应**: [examples/demo/chat_agent_demo.py](../examples/demo/chat_agent_demo.py)

### 应用示例
- **代码助手**: [examples/app/code_assistant/](../examples/app/code_assistant/)
- **深度研究**: [examples/app/deep_research/](../examples/app/deep_research/)
- **个人助手**: [examples/app/personal_assistant/](../examples/app/personal_assistant/)

## 🔍 常见问题

### Q: 如何选择合适的AI厂商？
**A**: 参考 [工具调用完整指南](./tool_call_documentation.md#不同厂商工具格式对比) 的详细对比表。

### Q: 工具调用失败如何调试？
**A**: 查看 [API 参考文档](./tool_call_api_reference.md#错误处理) 的错误处理部分。

### Q: 如何自定义工具？
**A**: 参考 [API 参考文档](./tool_call_api_reference.md#自定义工具) 的详细示例。

### Q: Schema 验证错误如何解决？
**A**: 查看 [Schema 规范文档](./schema_specification.md#验证和错误处理) 的验证部分。

## 🤝 贡献指南

### 报告问题
- 使用 GitHub Issues 报告 bug
- 提供完整的错误信息和复现步骤
- 包含环境信息（Python版本、依赖版本等）

### 提交功能请求
- 描述具体的使用场景
- 说明期望的API设计
- 提供相关的技术资料

### 代码贡献
- Fork 仓库并创建功能分支
- 遵循现有的代码风格
- 添加必要的测试和文档
- 提交 Pull Request

## 📞 支持和反馈

- **文档问题**: 在对应文档文件中提出 Issue
- **代码问题**: 在主仓库提出 Issue
- **功能建议**: 发送邮件或提出 Feature Request
- **社区讨论**: 加入相关技术群组

## 📜 许可证

本文档遵循 MIT 许可证，详见项目根目录的 LICENSE 文件。

---

**最后更新**: 2024年6月12日  
**文档版本**: 1.0.0  
**适用框架版本**: MengLong >= 1.0.0
