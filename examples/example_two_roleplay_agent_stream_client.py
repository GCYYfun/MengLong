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
from mlong.agent.role_play.two_role_play_agent import TwoRolePlayAgent

# 设置页面标题
st.title("Two RolePlay Agent")

# 初始化对话历史
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# 读取角色yaml文件
# with open("examples/example_configs/two_npc.yaml", "r") as f:
#     role_info = yaml.safe_load(f)

# role_info_a = {"role_system": role_info["a_role_system"], "role": role_info["a_role"]}
# role_info_b = {"role_system": role_info["b_role_system"], "role": role_info["b_role"]}

# a_rpa = RolePlayAgent(role_info=role_info_a)
# b_rpa = RolePlayAgent(role_info=role_info_b)

# topic = role_info["topic"]

# trpa = TwoRolePlayAgent(active_role=a_rpa, passive_role=b_rpa, topic=topic)

# 显示对话历史
# for message in st.session_state.messages:
#     st.write(f"{message['sender']}: \n\n{message['text']}")
#     st.write(f"\n")

placeholder1 = st.empty()

# 彩色分割线
st.subheader("#", divider="rainbow")

# 用户输入框
user_input = st.text_input("Input", key="user_input")

# 提交按钮
if st.button("发送"):

    def agent_worlflow(url):
        try:
            json_data = {
                "active_role_name": "ac",
                "passive_role_name": "pa",
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
                    ac_id = 0
                    pa_id = 0
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
                                if ac_id % 2 == 0:
                                    ac_id += 1
                                    role = f"ac-{ac_id}"
                                else:
                                    pa_id += 1
                                    role = f"pa-{pa_id}"
                                value = f"[{role}]\n\n"

                            if value.startswith("stop"):
                                value = "\n\n[结束]\n\n"
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

    agent_worlflow("http://127.0.0.1:8000/agent/tworoleplay")
