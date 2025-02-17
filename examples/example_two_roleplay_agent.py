import os
import sys
import streamlit as st
import yaml


# 设置项目根目录, 使得可以直接import mlong
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from mlong.agent.role_play.role_play_agent import RolePlayAgent
from mlong.agent.role_play.two_role_play_agent import TwoRolePlayAgent

# 设置页面标题
st.title("Two RolePlay Agent")

# 初始化对话历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 读取角色yaml文件
with open("examples/example_configs/two_npc.yaml", "r") as f:
    role_info = yaml.safe_load(f)

role_info_a = {"role_system": role_info["a_role_system"], "role": role_info["a_role"]}
role_info_b = {"role_system": role_info["b_role_system"], "role": role_info["b_role"]}

a_rpa = RolePlayAgent(role_info=role_info_a)
b_rpa = RolePlayAgent(role_info=role_info_b)

topic = role_info["topic"]

trpa = TwoRolePlayAgent(active_role=a_rpa, passive_role=b_rpa, topic=topic)

# 显示对话历史
for message in st.session_state.messages:
    st.write(f"{message['sender']}: \n\n{message['text']}")
    st.write(f"\n")

# 彩色分割线
st.subheader("#", divider="rainbow")

# 用户输入框
user_input = st.text_input("Input", key="user_input")

# 提交按钮
if st.button("发送"):
    if user_input.strip():
        # # 添加用户消息到对话历史
        # st.session_state.messages.append({"sender": "我", "text": user_input})
        # raw_input = user_input
        # format_input = f"""
        # 当前环境: 宗族的讲法广场上, 你正在和gt对话
        # gt是宗族新近的天才子弟, 他有着一双炯炯有神的眼睛, 头发乌黑, 为人老实，有毅力。
        # gt说:{raw_input}
        # """
        # # 模拟一个简单的机器人回答
        # # bot_response = rpa.step(format_input)
        # bot_response = trpa.chat()
        # print(bot_response)
        # st.session_state.messages.append(
        #     {"sender": f"{role_info["role"]["name"]}", "text": bot_response}
        # )
        bot_response = trpa.chat()
        print(bot_response)
        for message in bot_response:
            st.session_state.messages.append(
                {"sender": f"{message['role']}", "text": message["content"]}
            )

    # 刷新
    st.rerun()
