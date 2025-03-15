from mlong.model_interface import Model
from mlong.model_interface.utils import user

model = Model()
res = model.chat(messages=[user("你好")],model_id="us.deepseek.r1-v1:0")
print(res)
