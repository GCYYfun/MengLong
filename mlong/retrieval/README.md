# Retrieval 检索模块

retrieval 模块提供了高效的信息检索功能，使智能体能够从各种数据源中获取和处理信息，增强对话和决策能力。

## 模块结构

- **search/**: 搜索引擎相关实现
- **vector/**: 向量检索相关实现

## 搜索 (search/)

search 子模块提供了基于关键词的搜索能力，可以连接到各种搜索引擎或本地搜索系统。

主要功能：
- 关键词查询
- 搜索结果排序与过滤
- 搜索上下文管理

## 向量检索 (vector/)

vector 子模块实现了基于语义的向量检索功能，能够根据语义相似度查找相关信息。

主要功能：
- 文本向量化
- 相似度计算
- 向量索引管理
- 高效的最近邻搜索

## 使用场景

retrieval 模块可用于多种场景：

1. **知识库查询**: 智能体可以检索内部知识库获取信息
2. **记忆增强**: 与记忆系统结合，提供基于相关性的记忆检索
3. **参考资料引用**: 在生成响应时引用相关参考资料
4. **事实核查**: 验证生成内容的准确性

## 使用示例

```python
# 示例代码将在具体实现完成后补充
# 向量检索示例
from mlong.retrieval.vector import VectorRetrieval

# 初始化向量检索系统
retriever = VectorRetrieval(embedding_model="text-embedding-ada-002")

# 添加文档到索引
retriever.add_document("doc1", "人工智能是研究如何使计算机能够像人一样思考和学习的科学。")
retriever.add_document("doc2", "机器学习是人工智能的一个子领域，专注于让计算机从数据中学习。")

# 检索相关文档
results = retriever.query("什么是AI？", top_k=3)
for doc_id, score in results:
    print(f"文档ID: {doc_id}, 相关度: {score}")
```

## 与其他模块的集成

retrieval 模块可以与框架的其他组件紧密集成：

- 与 **memory** 模块结合用于智能记忆检索
- 与 **agent** 模块结合用于增强智能体的知识获取能力
- 与 **tools** 模块结合用于提供更全面的工具功能

## 未来扩展

计划中的功能扩展：
- 混合检索策略（关键词 + 向量）
- 分布式索引支持
- 多模态内容检索（图像、音频等）
- 实时更新的动态索引