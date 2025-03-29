# MengLong 前端项目

这是MengLong框架的前端项目，用于与后端API进行交互，提供用户友好的Web界面。

## 计划功能

- 聊天界面，支持多轮对话
- 角色扮演系统
- 记忆增强的对话系统
- 代理对话可视化
- 向量数据库管理界面
- RAG系统的文档上传和查询

## 技术栈推荐

- **React** / **Vue.js** - 前端框架
- **TypeScript** - 类型安全
- **Tailwind CSS** - 样式系统
- **Axios** - API请求
- **Socket.io** - 流式响应处理

## 目录结构（计划）

```
frontend/
├── public/
├── src/
│   ├── components/
│   │   ├── Chat/
│   │   ├── Agent/
│   │   ├── RAG/
│   │   └── VectorDB/
│   ├── pages/
│   ├── services/
│   │   └── api/
│   ├── store/
│   ├── types/
│   ├── utils/
│   ├── App.tsx
│   └── main.tsx
├── package.json
└── README.md
```

## 开发计划

1. 搭建基础项目结构
2. 实现API服务对接
3. 开发基础聊天界面
4. 开发角色扮演功能
5. 实现流式响应
6. 添加RAG和向量数据库功能
7. 优化UI/UX
8. 测试和部署

## 与后端API集成

前端将通过HTTP请求与后端API交互，基本流程如下：

1. 使用Axios或Fetch API发送HTTP POST请求到相应的API端点
2. 请求头应包含 `Content-Type: application/json`
3. 使用异步/await或Promise处理响应
4. 对于流式响应，将使用WebSocket或SSE(Server-Sent Events)

## 贡献指南

欢迎贡献代码、报告问题或提出改进建议。请确保代码符合项目的代码风格和最佳实践。

## 许可证

MIT License 