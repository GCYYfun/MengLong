import asyncio
import json
import os
import re
import sys
import streamlit as st
import yaml


# 设置项目根目录, 使得可以直接import mlong
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from mlong.agent.role_play.role_play_agent import RolePlayAgent

# 设置页面标题
st.title("RolePlay Agent")

# 初始化对话历史
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# 读取角色yaml文件
with open("examples/example_configs/default_npc.yaml", "r") as f:
    role_info = yaml.safe_load(f)

rpa = RolePlayAgent(role_info=role_info)

# # 显示对话历史
# for message in st.session_state.messages:
#     st.write(f"{message['sender']}: {message['text']}")
placeholder1 = st.empty()
st.subheader("#", divider="rainbow")
placeholder2 = st.empty()

# 彩色分割线
st.subheader("#", divider="rainbow")

# 用户输入框
user_input = st.text_input("Input", key="user_input")

# 提交按钮
if st.button("发送"):
    if user_input.strip():
        # 添加用户消息到对话历史
        # st.session_state.messages.append({"sender": "我", "text": user_input})
        raw_input = user_input
        format_input = f"""
        当前环境: 宗族的讲法广场上, 你正在和gt对话
        gt是宗族新近的天才子弟, 他有着一双炯炯有神的眼睛, 头发乌黑, 为人老实，有毅力。
        gt说:{raw_input}
        """
        full_text = ""

        # 模拟一个简单的机器人回答
        bot_response = rpa.chat_stream(format_input)

        async def parse_response(response):
            # 将输入的提示按句子分割
            s = response.stream
            if s:
                for event in s:
                    # 将事件转换为字典
                    # event = await event.json()
                    if "contentBlockDelta" in event:
                        delta = event["contentBlockDelta"]
                        if "delta" in delta and "text" in delta["delta"]:
                            yield f"data:{json.dumps({"data":delta['delta']['text']})}\n\n"
                    # if "messageStart" in event:
                    #     message_start = event["messageStart"]
                    #     role = message_start["role"]
                    #     yield f"data:{json.dumps({"data":"["+role+"]:"})}\n\n"

        async def event_generator(bot_response):
            async for item in parse_response(bot_response):
                item = item.strip()
                value = ""
                if re.match(r"^data:", item, re.DOTALL):
                    value = re.sub(r"^data:", "", item)
                    value = json.loads(value)["data"]
                    st.session_state["messages"].append(value)
                yield value
                await asyncio.sleep(0)

        placeholder1.write_stream(event_generator(bot_response))

        full_text = "".join(st.session_state["messages"])
        print(full_text)
        placeholder1.empty()
        placeholder1.write(full_text)
        rpa.chat_man.add_assistant_response(full_text)
        st.session_state["messages"].clear()

        format_input_2 = f"""
        当前环境: 宗族的讲法广场上, 你正在和gt对话
        gt是宗族新近的天才子弟, 他有着一双炯炯有神的眼睛, 头发乌黑, 为人老实，有毅力。
        gt说:师傅在上，受徒一拜！
        """
        bot_response2 = rpa.chat_stream(format_input_2)
        placeholder2.write_stream(event_generator(bot_response2))
        full_text = "".join(st.session_state["messages"])
        print(full_text)
        placeholder2.empty()
        placeholder2.write(full_text)
        rpa.chat_man.add_assistant_response(full_text)
        st.session_state["messages"].clear()

        # print(bot_response)
        # st.session_state.messages.append(
        #     {"sender": f"{role_info["role"]["name"]}", "text": bot_response}
        # )

    # 刷新
    # st.rerun()
