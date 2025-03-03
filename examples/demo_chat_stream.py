from mlong.model_interface import Model
from mlong.model_interface.utils import user

model = Model()
res = model.chat(messages=[user("你好")], stream=True)

s = res.stream
for event in s:
    if "contentBlockDelta" in event:
        print(event["contentBlockDelta"]["delta"]["text"], end="")
