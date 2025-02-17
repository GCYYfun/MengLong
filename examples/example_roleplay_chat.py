import os
import sys
import streamlit as st
import yaml


# 设置项目根目录, 使得可以直接import mlong
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from mlong.agent.role_play.role_play_agent import RolePlayAgent
from mlong.model import Model

# 设置页面标题
st.title("RolePlay对话")
# 初始化对话历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 读取角色yaml文件
with open("examples/example_configs/default_npc.yaml", "r") as f:
    role_info = yaml.safe_load(f)

rpa = RolePlayAgent(role_info=role_info)

# 显示对话历史
for message in st.session_state.messages:
    st.write(f"{message['sender']}: {message['text']}")

# 彩色分割线
st.subheader("#", divider="rainbow")

# 用户输入框
user_input = st.text_input("Input", key="user_input")

# 提交按钮
if st.button("发送"):
    if user_input.strip():
        # 添加用户消息到对话历史
        st.session_state.messages.append({"sender": "我", "text": user_input})

        # 模拟一个简单的机器人回答
        bot_response = rpa.chat(user_input)
        print(bot_response)
        st.session_state.messages.append(
            {"sender": f"{role_info["role"]["name"]}", "text": bot_response}
        )

    # 刷新
    st.rerun()
