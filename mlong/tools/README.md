# Tools 工具模块

tools 模块提供了各种工具的集成，扩展智能体的能力范围，使其能够执行特定任务和与外部系统交互。

## 模块结构

- **python_interpreter.py**: Python解释器工具
- **vector_database.py**: 向量数据库工具
- **database/**: 数据库相关工具

## 主要工具

### Python解释器 (python_interpreter.py)

Python解释器工具允许智能体执行Python代码，使其能够：
- 执行计算
- 处理数据
- 调用外部API
- 创建和测试代码片段

使用此工具可以让智能体在与用户交互过程中执行实际的编程任务。

### 向量数据库 (vector_database.py)

向量数据库工具提供了存储和检索向量化数据的能力，常用于：
- 语义搜索
- 相似度计算
- 知识库管理
- 记忆增强

### 数据库工具 (database/)

数据库工具提供了与各种数据库系统交互的能力，支持：
- SQL查询
- 数据插入和更新
- 结构化数据管理
- 事务处理

## 工具调用机制

工具调用遵循以下流程：

1. 智能体分析用户需求，决定需要调用的工具
2. 准备工具所需的参数
3. 调用工具并获取结果
4. 处理结果并将其整合到响应中

## 使用示例

### Python解释器

```python
from mlong.model import Model
from mlong.agent.agent import Agent
from mlong.tools.python_interpreter import PythonInterpreter

# 创建模型和智能体
model = Model()
agent = Agent(model=model)

# 添加Python解释器工具
python_tool = PythonInterpreter()
agent.add_tool("python", python_tool)

# 使用工具执行代码
response = agent.chat("计算斐波那契数列的前10个数")
# 智能体将能够执行Python代码计算斐波那契数列
```

### 向量数据库

```python
from mlong.tools.vector_database import VectorDatabase

# 初始化向量数据库
# 创建集合
vector_db = VectorStore.create_collection("ai_docs")

# 添加文档（带元数据）
vector_db.add_documents(
    documents=[
        "人工智能基础概念与应用",
        "深度学习在自然语言处理中的应用"
    ],
    metadatas=[
        {"category": "基础理论"},
        {"category": "应用实践"}
    ]
)

# 带过滤条件的查询
results = vector_db.query_documents(
    "机器学习应用",
    top_k=3,
    filter_conditions={"category": "应用实践"}
)
for result in results:
    print(f"文档ID: {result['id']}, 相似度: {result['score']:.2f}")
    print(f"元数据: {result['metadata']}")
```

## 添加新工具

要添加新工具：

1. 创建新的工具类文件
2. 实现必要的接口方法（通常包括`__call__`方法）
3. 提供适当的文档和示例
4. 确保错误处理和参数验证

工具设计应遵循以下原则：
- 职责单一
- 接口清晰
- 错误处理完善
- 文档完整