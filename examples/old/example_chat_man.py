import os, sys, yaml

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mlong.agent.role_play.yao_guang import YaoGuang
from mlong.utils import stream_to_str


with open(os.path.join("examples", "example_configs", "default_npc.yaml"), "r") as f:
    role_info = yaml.safe_load(f)

yg = YaoGuang(
    role_info=role_info,
    memory_file=os.path.join("examples", "example_configs", "yaogunag.json"),
)

res = yg.chat_stream("你好")
print(stream_to_str(res))
res = yg.chat_stream("我想拜你为师")
print(stream_to_str(res))
yg.summary()
