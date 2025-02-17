import os


class Vectorstore:
    def __init__(self, name):
        self.name = name
        self.embeddings = []
        self.metadata = []
        self.db_path = f"./database/{name}.pkl"

        # embedding model : cohere.embed-multilingual-v3
        # rerank model : cohere.rerank-v3-5:0

    def connect(self):
        pass

    def xxx(self):
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
        pass

    def search(self):
        pass

    def save():
        pass
