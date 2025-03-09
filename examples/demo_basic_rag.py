from mlong.tools.vector_database import VectorStore
from typing import List
import re

class BasicRAGDemo:
    def __init__(self):
        self.vector_db = VectorStore()
        self.vector_db.connect_collection("knowledge_base")

    def _text_chunker(self, text: str, chunk_size: int = 500) -> List[str]:
        """简单文本分块器，按标点分割"""
        sentences = re.split(r'(?<=[。！？])\s*', text)
        chunks = []
        current_chunk = []
        
        for sent in sentences:
            if sum(len(s) for s in current_chunk) + len(sent) > chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
            current_chunk.append(sent)
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        return chunks

    def ingest_documents(self, raw_text: str):
        """文档预处理管道"""
        # 文本分块
        chunks = self._text_chunker(raw_text)
        
        # 创建唯一ID
        doc_ids = [f"doc_{i}" for i in range(len(chunks))]
        
        # 存储到向量库
        self.vector_db.add_documents(
            ids=doc_ids,
            documents=chunks,
            metadatas=[{"source": "demo"} for _ in chunks]
        )
        print(f"✅ 成功存储 {len(chunks)} 个文本块")

    def query(self, question: str) -> str:
        """检索增强的问答流程"""
        # 1. 检索相关文档
        results = self.vector_db.query(
            question,
            top_k=3,
            filter_conditions={"source": "demo"}
        )
        
        # 2. 构建上下文
        context = "\n".join([
            self.vector_db.data[r['id']]['document']
            for r in results
        ])
        
        # 3. 生成增强回答（此处简化为模板，实际应调用LLM）
        response = f"""基于以下知识库内容：
{context}

问题：{question}
答案：已找到{len(results)}条相关记录，具体内容如上所示。"""
        
        return response

if __name__ == "__main__":
    # 示例文档
    sample_text = """人工智能(Artificial Intelligence, AI)是模拟人类智能的系统。机器学习是AI的子领域，通过数据训练模型。
    深度学习利用神经网络进行特征学习。自然语言处理(NLP)使计算机能理解人类语言。"""

    rag_system = BasicRAGDemo()
    
    print("\n==== 文档摄入阶段 ====")
    rag_system.ingest_documents(sample_text)
    
    print("\n==== 问答测试 ====")
    test_question = "深度学习和机器学习有什么关系？"
    answer = rag_system.query(test_question)
    
    print("\n生成回答：")
    print(answer)
    print("\n✨ RAG演示完成！")