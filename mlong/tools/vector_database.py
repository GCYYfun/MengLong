import os
import pickle

from mlong.model import Model


class VectorStore:
    def __init__(self, name):
        self.name = name  # db name
        self.model = Model()
        self.embeddings = []
        self.metadata = []
        self.db_path = f"./database/{name}.pkl"

        # embedding model : cohere.embed-multilingual-v3
        # rerank model : cohere.rerank-v3-5:0

    def connect(self, name=None):
        if self.embeddings and self.metadata:
            print("Vector database is already loaded. Skipping data loading.")
            return
        if name:
            self.name = name
            self.db_path = f"./database/{name}.pkl"
        if os.path.exists(self.db_path):
            print(f"Loading vector database from {self.db_path}")
            self.load()
            return

    def close(self):
        if self.embeddings and self.metadata:
            print("Vector database is already loaded. Skipping data loading.")
            return
        if os.path.exists(self.db_path):
            print(f"Loading vector database from {self.db_path}")
            self.load()
            return

    def add(self, data):
        if self.embeddings and self.metadata:
            print("Vector database is already loaded. Skipping data loading.")
            return
        if os.path.exists(self.db_path):
            print(f"Loading vector database from {self.db_path}")
            self.load()
            return
        texts = []
        self.embed_and_store(texts)
        self.save()
        print(f"Vector database is saved to {self.db_path}")

    def embed_and_store(self, texts):
        batch_size = 32

        self.embeddings = []
        self.metadata = []
        pass

    def load(self):
        if not os.path.exists(self.db_path):
            # raise FileNotFoundError(f"Vector database not found at {self.db_path}")
            print(f"Vector database not found at {self.db_path} , creating new one.")
            # create new db
            # 创建文件
            with open(self.db_path, "wb") as f:
                pass
        else:
            print(f"Loading vector database from {self.db_path}")
            with open(self.db_path, "rb") as f:
                data = pickle.load(f)
                self.metadata = data["metadata"]
                self.embeddings = data["embeddings"]

        pass

    def search(self):
        pass

    def save():
        pass
