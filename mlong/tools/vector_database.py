import os
import pickle

from typing import List, Dict, Optional, Any, TypedDict

from mlong.model_interface.model import Model

CURR_DIR = os.path.dirname(os.path.abspath(__file__))


class DocumentEntry(TypedDict):
    document: str
    embedding: List[float]
    metadata: Optional[Dict[str, Any]]


class VectorStore:
    # Model
    # dim 1024 
    # max token 512
    def __init__(self, collection_name: Optional[str] = None) -> None:
        self.collection_name: Optional[str] = None
        self.model: Model = Model()
        self.data: Dict[str, DocumentEntry] = {}
        self.db_path: Optional[str] = None  # 数据库文件存储路径
        self._connected: bool = False

    def connect_collection(self, collection_name: str) -> None:
        """
        Connect to the vector collection
        """
        # 如果正在连接一个集合，先保存断开
        if self._connected:
            self.save()
            self.data.clear()
        self.collection_name = collection_name
        self.db_path = f"{CURR_DIR}/database/{collection_name}.pkl"
        self._connected = True
        if os.path.exists(self.db_path):
            print(f"加载 {collection_name} 数据库")
            self.load()
        else:
            # Create empty collection file
            print(f"创建 {collection_name} 数据库")
            with open(self.db_path, "wb") as f:
                pickle.dump({}, f)

    def close(self):
        """
        Close the connection to the collection
        """
        self.save()
        self.data.clear()
        self._connected = False

    @property
    def ids(self):
        return [i for i in self.data.keys()]
    @property
    def documents(self):
        return [doc["document"] for doc in self.data.values()] # python3.12 dict 有序
    @property
    def metadata(self):
        return [doc["metadata"] for doc in self.data.values()]
    @property
    def embeddings(self):
        return [doc["embedding"] for doc in self.data.values()]

    # @classmethod
    # def create_collection(cls, name, metadata_config=None):
    #     """
    #     Create a new collection
    #     :param name: Collection identifier
    #     :param metadata_config: Optional metadata schema configuration
    #     """
    #     db_path = f"{CURR_DIR}/database/{name}.pkl"
    #     print(db_path)
    #     if os.path.exists(db_path):
    #         raise ValueError(f"Collection {name} already exists")
    #     # Create empty collection file
    #     with open(db_path, "wb") as f:
    #         pickle.dump({}, f)
    #     return cls(name)

    @staticmethod
    def list_collections() -> List[str]:
        """List all available collections in the database directory"""
        collections = []
        db_dir = f"{CURR_DIR}/database"
        if os.path.exists(db_dir):
            for fname in os.listdir(db_dir):
                if fname.endswith(".pkl"):
                    collections.append(fname[:-4])
        print(collections)
        return collections

    def add_documents(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: Optional[List[List[float]]] = None,
        metadatas: Optional[List[Optional[Dict[str, Any]]]] = None
    ) -> None:
        """
        Add documents to the collection
        :param documents: List of documents to add
        :param embeddings: Optional list of embeddings corresponding to the documents
        :param metadatas: Optional list of metadata corresponding to the documents
        """
        if not self._connected:
            raise ValueError("未连接到集合")
        # 提供文档，生成文本嵌入
        if not embeddings:
            # 文档 和 嵌入向量 数量必须一致
            if len(documents) != len(ids):
                raise ValueError("文档数量与嵌入向量数量不匹配")
            embeddings = self.model.embed(documents).embeddings
        else:
            # 文档 和 嵌入向量 数量必须一致
            if len(documents) != len(embeddings):
                raise ValueError("文档数量与嵌入向量数量不匹配")

        for i, id in enumerate(ids):
            self.data[id] = {
                "document": documents[i],
                "embedding": embeddings[i],
                "metadata": metadatas[i] if metadatas else {},
            }

        self.save()

    def query(
        self,
        query_text: Optional[str] = None,
        query_embedding: Optional[List[float]] = None,
        top_k: int = 5,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        if not query_embedding and query_text:
            query_embedding = self.model.embed([query_text]).embeddings[0]

        # 元数据过滤
        filtered_indices = [
            i
            for i, meta in enumerate(self.metadata)
            if all(meta.get(k) == v for k, v in (filter_conditions or {}).items())
        ]

        # 计算相似度
        scores = [
            (i, self._cosine_similarity(query_embedding, emb))
            for i, emb in enumerate(self.embeddings)
            if i in filtered_indices
        ]

        # 排序并返回结果
        sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)[:top_k]
        return [
            {
                "id": self.ids[i],
                "score": score,
                "metadata": {k: v for k, v in (self.metadata[i] or {}).items()},
            }
            for i, score in sorted_scores
        ]

    def delete_document(self, document_id: str) -> None:
        """
        Delete a document from the collection
        :param document_id: ID of the document to delete
        """
        if document_id in self.data:
            self.data.pop(document_id, None)
        self.save()

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """
        计算余弦相似度
        这里假设 a 和 b 是两个向量
        a = [1, 2, 3]
        b = [4, 5, 6]
        欧几里得点积： a · b = ||a|| * ||b|| * cos(θ)
        cosine_similarity(a, b) = (1*4 + 2*5 + 3*6) / (sqrt(1^2 + 2^2 + 3^2) * sqrt(4^2 + 5^2 + 6^2))

        """

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x**2 for x in a) ** 0.5
        norm_b = sum(x**2 for x in b) ** 0.5
        return dot_product / (norm_a * norm_b)

    def load(self) -> None:
        with open(self.db_path, "rb") as f:
            self.data = pickle.load(f)

    def save(self) -> None:
        with open(self.db_path, "wb") as f:
            pickle.dump(self.data, f)
