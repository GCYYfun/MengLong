import asyncio
import json
import os
import re
import sys
import requests
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

        def agent_worlflow(url):
            try:
                json_data = {
                    "role_name": "template",
                    "model_id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                    "messages": [
                        {
                            "role": "user",
                            "content": "hello,output 1000 word!,include markdown \n json \n something \n\n,else special format.",
                        }
                    ],
                    "temperature": 0.5,
                    "maxTokens": 8192,
                    "stream": True,
                }
                # 发送 Post 请求，启用流式模式

                with requests.post(
                    url, json=json_data, stream=True, timeout=20
                ) as response:
                    # 确保请求成功
                    response.raise_for_status()

                    def parse_stream():
                        for line in response.iter_lines(decode_unicode=True):
                            # 处理服务器 Server-Sent Events  格式数据

                            #     if pending is not None:
                            #         chunk = pending + chunk

                            #     if delimiter:
                            #         lines = chunk.split(delimiter)
                            #     else:
                            #         lines = chunk.splitlines()

                            #     if lines and lines[-1] and chunk and lines[-1][-1] == chunk[-1]:
                            #         pending = lines.pop()
                            #     else:
                            #         pending = None

                            #     yield from lines

                            # if pending is not None:
                            #     yield pending
                            # print(repr(line))
                            value = ""
                            if re.match(r"^data:", line, re.DOTALL):
                                value = re.sub(r"^data:", "", line)
                                value = json.loads(value)["data"]
                            if re.match(r"^event:", line, re.DOTALL):
                                value = re.sub(r"^event:", "", line)
                                value = json.loads(value)["event"]
                                if value.startswith("start"):
                                    value = "[开始]\n"
                                if value.startswith("stop"):
                                    value = "\n[结束]\n"
                            # elif re.match(r"^event:", line, re.DOTALL):
                            #     value = re.sub(r"^event:", "", line)
                            # elif re.match(r"^id:", line, re.DOTALL):
                            #     value = re.sub(r"^id:", "", line)
                            yield value

                    placeholder1.write_stream(parse_stream())
                # response.iter_lines(decode_unicode=True))
                # 逐行读取响应内容
                # for line in response.iter_content(decode_unicode=True):
                #     if line:
                #         print(line, end="", flush=True)

            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")

        agent_worlflow("http://127.0.0.1:8000/test/multi")
