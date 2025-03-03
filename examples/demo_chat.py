from mlong.model_interface import Model
from mlong.model_interface.utils import user

model = Model()
res = model.chat(messages=[user("你好")])
print(res)
