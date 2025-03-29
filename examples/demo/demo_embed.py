from mlong.model_interface import Model

# 初始化Model实例（使用Amazon Titan嵌入模型）
# try:
# 创建模型实例并指定嵌入模型
model = Model()

# 需要计算嵌入的文本
text = "自然语言处理是人工智能的重要领域"

# 调用嵌入接口
response = model.embed(texts=[text])

# 提取并打印嵌入向量
if response:
    print(f"文本嵌入维度: {len(response.embeddings[0])}")
    print(f"前5个维度值: {response.embeddings[:5]}")
else:
    print("未获取到有效的嵌入向量")
