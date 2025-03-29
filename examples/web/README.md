# MengLong Web应用

这是基于MengLong框架的Web应用项目，包含前后端实现，旨在提供一个完整的大模型应用平台。

## 项目结构

```
web/
├── backend/        # FastAPI后端服务
│   ├── server.py   # 主服务器代码
│   └── README.md   # 后端文档
├── frontend/       # 前端项目
│   └── README.md   # 前端文档
└── README.md       # 本文档
```

## 功能概述

本项目基于MengLong框架，提供以下核心功能：

- 多种大模型的对话接口
- 角色扮演和代理对话系统
- 基于FluctLight的记忆增强对话
- 向量数据库存储与检索
- 检索增强生成(RAG)系统

## 快速开始

### 启动后端服务

```bash
cd backend
pip install -r requirements.txt
python server.py
```

服务将在 http://localhost:8000 启动，API文档可以在 http://localhost:8000/docs 访问。

### 前端开发（计划中）

前端项目目前处于规划阶段，具体实现请参考frontend目录下的README文档。

## 技术栈

- **后端**: FastAPI, Python, MengLong框架
- **前端**: (计划) React/Vue.js, TypeScript, Tailwind CSS
- **数据库**: 向量数据库

## 开发路线图

1. ✅ 完成后端API实现
2. ✅ 编写文档
3. ⬜ 实现前端基础功能
4. ⬜ 完善前后端交互
5. ⬜ 优化用户体验
6. ⬜ 添加更多高级功能

## 贡献指南

欢迎贡献代码、报告问题或提出改进建议。请确保按照各自目录中的README文档进行操作。

## 许可证

MIT License

## 相关链接

- [MengLong框架文档](https://github.com/yourusername/MengLong)
- [演示项目](https://github.com/yourusername/MengLong/examples/demo) 