import os, sys, yaml

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mlong.agent.role_play.yao_guang import YaoGuang
from mlong.utils import stream_to_str


with open(os.path.join("examples", "example_configs", "default_npc.yaml"), "r") as f:
    role_info = yaml.safe_load(f)

yg = YaoGuang(
    role_info=role_info,
    st_memory_file=os.path.join("examples", "example_configs", "yaogunag_st.json"),
    wm_memory_file=os.path.join("examples", "example_configs", "yaogunag_wm.json"),
)

res = yg.chat_with_mem("你好,我是cx，112")
print(yg.system_prompt)
print(res)
# print(stream_to_str(res))
# yg.summary()
# yg.chat_man.clear()
# res = yg.chat_stream_with_mem("112")
# print(stream_to_str(res))
