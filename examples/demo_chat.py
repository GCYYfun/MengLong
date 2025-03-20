from mlong.model_interface import Model
from mlong.model_interface.utils import user

model = Model()
res = model.chat(messages=[user("你好,你是谁？简单回复一下")],model_id="deepseek-reasoner",temperature=1.3)
print(res)

# 支持的模型
# Claude-3.7-Sonnet
# us.deepseek.r1-v1:0
# deepseek-reasoner
# deepseek-chat
# gpt-4o
# claude-3-5-sonnet-20241022
# us.amazon.nova-pro-v1:0
# us.anthropic.claude-3-5-sonnet-20241022-v2:0
# us.anthropic.claude-3-7-sonnet-20250219-v1:0
# cohere.embed-multilingual-v3
