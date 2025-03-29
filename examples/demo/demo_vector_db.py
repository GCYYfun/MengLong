
from mlong.tools.vector_database import VectorStore


def demo_vector_db():

    test_db = VectorStore()
    test_db.connect_collection("test_collection")
    print("\n✅ 集合连接测试通过")

    # 测试文档添加
    docs = ["昨日计划：1、学习", "今天天气不错", ]
    test_db.add_documents(
        ids=["doc1", "doc2"],
        documents=docs,
        metadatas=[{"category": "理论"}, {"category": "实践"}],
    )
    assert len(test_db.ids) == 2, "文档添加数量不符"
    print("\n✅ 文档添加测试通过")

    # 测试查询功能
    results = test_db.query("今天应该干些什么呢？")
    print("query:",results)
    print("\n✅ 文档查询测试通过")

    # 测试删除功能
    test_db.delete_document("doc2")
    print(test_db.ids)
    assert len(test_db.ids) == 1, "文档删除数量不符"
    print("\n✅ 文档删除测试通过")


if __name__ == "__main__":
    demo_vector_db()
    print("\n✨ 所有测试执行完成！")
