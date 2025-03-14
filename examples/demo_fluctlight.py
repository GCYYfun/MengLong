import os
import sys
import yaml

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mlong.agent.role import FluctLight


role_config = {
    "id": "Alice",
    "role_system": "你是一个中国${gender}性，你的名字叫${name}。\n\n${topic}\n\n${daily_logs}",
    "role_info": {"name": "Alice", "gender": "女", "age": "18"},
    "role_var": {"topic": "", "daily_logs": ""},
}

yg = FluctLight(
    role_config=role_config,
    st_memory_file=os.path.join(os.path.dirname(__file__), "yaogunag_st.yaml"),
    wm_memory_file=os.path.join(os.path.dirname(__file__), "yaogunag_wm.yaml"),
)


print("输入'exit'退出对话")
while True:
    message = input("\n请输入消息：")
    if message.lower() == 'exit':
        yg.summary()
        break
    if message.lower() == 'clear':
        yg.clear()
        break
    res = yg.chat_with_mem(message)
    print(f"\n[系统提示更新]\n{yg.system_prompt}\n")
    print(f"[回复] {res}\n")
