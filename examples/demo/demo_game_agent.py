import os
import sys
import yaml

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mlong.agent.role_play import GameAgent


# 角色配置
role_config = {
    "id": "Alice",
    "role_system": "你是一个中国${gender}性，你的名字叫${name}。\n\n${topic}\n\n${daily_logs}",
    "role_info": {"name": "Alice", "gender": "女", "age": "18"},
    "role_var": {"topic": "", "daily_logs": ""},
}

# 确保configs目录存在
configs_dir = os.path.join(os.path.dirname(__file__), "configs")
if not os.path.exists(configs_dir):
    os.makedirs(configs_dir)

# 使用configs目录中的记忆文件
fl = GameAgent(
    role_config=role_config,
    st_memory_file=os.path.join(configs_dir, "fl_st.yaml"),
    wm_memory_file=os.path.join(configs_dir, "fl_wm.yaml"),
)


print("输入'exit'退出对话")
while True:
    message = input("\n请输入消息：")
    if message.lower() == "exit":
        fl.summary()
        break
    if message.lower() == "clear":
        fl.clear()
        break
    res = fl.chat_with_mem(message)
    print(f"\n[系统提示更新]\n{fl.system_prompt}\n")
    print(f"[回复] {res}\n")
