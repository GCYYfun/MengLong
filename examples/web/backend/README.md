# MengLong API服务

这是一个基于FastAPI实现的MengLong框架API服务，提供了大模型对话、角色扮演、向量检索等功能的REST API接口。

## 功能特性

- 基础大模型对话API
- 角色扮演聊天API
- FluctLight记忆增强的角色扮演聊天
- 代理对话(Agent-to-Agent)
- 向量数据库存储与检索
- 检索增强生成(RAG)

## 安装与运行

### 环境要求

- Python 3.12+
- FastAPI

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务

```bash
cd /path/to/examples/web/backend
fastapi dev server.py
```

服务将在 http://localhost:8000 启动，API文档可以在 http://localhost:8000/docs 访问。

## API接口说明

### 基础对话API

**端点**: `/api/chat`  
**方法**: POST  
**功能**: 与大模型进行基础对话

请求示例:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "你好，请介绍一下自己"
    }
  ],
  "model_id": "Claude-3.7-Sonnet",
  "stream": false
}
```

### 角色扮演聊天API

**端点**: `/api/agent/chat`  
**方法**: POST  
**功能**: 与角色扮演代理进行对话

请求示例:
```json
{
  "role_config": {
    "id": "Alice",
    "role_system": "你是一个中国${gender}性，你的名字叫${name}。\n\n${topic}\n\n${daily_logs}",
    "role_info": {
      "name": "Alice",
      "gender": "女",
      "age": "18"
    },
    "role_var": {
      "topic": "",
      "daily_logs": ""
    }
  },
  "message": "你好，请介绍一下自己"
}
```

### FluctLight记忆增强的角色扮演聊天API

**端点**: `/api/agent/fluctlight`  
**方法**: POST  
**功能**: 使用FluctLight进行有记忆功能的角色扮演对话

请求示例:
```json
{
  "role_config": {
    "id": "Alice",
    "role_system": "你是一个中国${gender}性，你的名字叫${name}。\n\n${topic}\n\n${daily_logs}",
    "role_info": {
      "name": "Alice",
      "gender": "女",
      "age": "18"
    },
    "role_var": {
      "topic": "",
      "daily_logs": ""
    }
  },
  "message": "你好，请介绍一下自己",
  "clear_memory": false
}
```

### 代理对话API

**端点**: `/api/agent/ata`  
**方法**: POST  
**功能**: 让两个角色之间进行对话

请求示例:
```json
{
  "active_role": {
    "id": "柳天天",
    "role_system": "你扮演一个${gender}性，名字叫${name}，年龄${age}岁。\n\n${topic}\n\n${daily_logs}",
    "role_info": {
      "name": "柳天天",
      "gender": "女",
      "age": "20"
    },
    "role_var": {
      "topic": "",
      "daily_logs": ""
    }
  },
  "passive_role": {
    "id": "叶凡",
    "role_system": "你扮演一个${gender}性，名字叫${name}，年龄${age}岁。\n\n${topic}\n\n${daily_logs}",
    "role_info": {
      "name": "叶凡", 
      "gender": "男", 
      "age": "25"
    },
    "role_var": {
      "topic": "",
      "daily_logs": ""
    }
  },
  "topic": "[任务] 与${peer_name}进行符合自己性格与背景的聊天，交互式聊天。\n[描述] 你正在和${peer_name}进行自然对话。不一定每句话都要回复。"
}
```

### 向量数据库API

**端点**: `/api/vectorstore`  
**方法**: POST  
**功能**: 存储文档到向量数据库或从向量数据库中检索内容

文档存储请求示例:
```json
{
  "collection_name": "knowledge_base",
  "documents": [
    "人工智能(Artificial Intelligence, AI)是模拟人类智能的系统。",
    "机器学习是AI的子领域，通过数据训练模型。",
    "深度学习利用神经网络进行特征学习。"
  ]
}
```

文档检索请求示例:
```json
{
  "collection_name": "knowledge_base",
  "query": "什么是深度学习？",
  "top_k": 3
}
```

### RAG查询API

**端点**: `/api/rag`  
**方法**: POST  
**功能**: 基于知识库进行检索增强生成回答

请求示例:
```json
{
  "question": "深度学习和机器学习有什么关系？",
  "collection_name": "knowledge_base"
}
```

## 前端集成指南

前端可以通过HTTP请求与后端API交互。基本流程如下:

1. 发送HTTP POST请求到相应的API端点
2. 请求头应包含 `Content-Type: application/json`
3. 请求体应按照上述示例的JSON格式提供

对于流式响应，需要使用WebSocket或SSE(Server-Sent Events)等技术进行实现。

## 开发者注意事项

- API接口在生产环境中应添加适当的身份验证和授权机制
- 对于大规模部署，请考虑使用负载均衡和容器化技术
- 向量数据库的数据持久化需要额外配置

## 常见问题

1. **Q: 如何更改服务器端口?**  
   A: 修改server.py文件中的`uvicorn.run`函数的port参数。

2. **Q: 如何添加自定义模型?**  
   A: 在ModelID枚举类中添加新的模型ID，并确保MengLong框架支持该模型。

3. **Q: 如何实现流式响应?**  
   A: 需要使用WebSocket或SSE实现，这需要额外的前端和后端代码。

## 许可证

MIT License 