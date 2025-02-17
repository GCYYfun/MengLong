import json
import os
import re
import sys
import time

import requests
import streamlit as st
import yaml


# 设置项目根目录, 使得可以直接import mlong
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# from mlong.agent.role_play.role_play_agent import RolePlayAgent
# from mlong.model import Model

# 设置页面标题
st.title("stream 对话")
# 初始化对话历史
if "messages" not in st.session_state:
    st.session_state.messages = []

stream_mode = True


def parse_stream(stream):
    print(type(stream))
    for line in stream.iter_lines():
        yield line.decode("utf-8")


# 显示对话历史
# for message in st.session_state.messages:
#     st.write(f"{message['sender']}: {message['text']}")
placeholder1 = st.empty()
# 彩色分割线
st.subheader("#", divider="rainbow")

# # 用户输入框
# user_input = st.text_input("Input", key="user_input")

# 提交按钮
if st.button("发送"):
    # if user_input.strip():
    # 添加用户消息到对话历史
    # st.session_state.messages.append({"sender": "我", "text": user_input})

    # 模拟一个简单的机器人回答
    # 向127.0.0.1:8000/chat 发送一个post请求
    # res = requests.post(
    #     "http://127.0.0.1:8000/chat",
    #     json={
    #         "model_id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    #         "messages": [{"role": "user", "content": "hello,output 1000 word!"}],
    #         "temperature": 0.5,
    #         "maxTokens": 8192,
    #         "stream": stream_mode,
    #     },
    # )
    from aiohttp import ClientSession
    from aiohttp import ClientError

    async def send_data():
        async with ClientSession() as session:
            json = {
                "model_id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                "messages": [{"role": "user", "content": "hello,output 100 word!"}],
                "temperature": 0.5,
                "maxTokens": 8192,
                "stream": stream_mode,
            }
            try:
                async with session.post(
                    "http://127.0.0.1:8000/chat", json=json
                ) as resp:
                    print(type(resp))
                    print(type(resp.content))
                    async for data in resp.content:
                        if data:
                            print(data, end="", flush=True)
                            placeholder1.write(data)
            except ClientError as e:
                print(f"Request failed: {e}")

    def listen_sse(url):
        try:
            json_data = {
                "model_id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                "messages": [
                    {
                        "role": "user",
                        "content": "hello,output 1000 word!,include markdown \n json \n something \n\n,else special format.",
                    }
                ],
                "temperature": 0.5,
                "maxTokens": 8192,
                "stream": stream_mode,
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

    listen_sse("http://127.0.0.1:8000/chat")

    # def ps():
    #     for line in res.iter_lines():
    #         if line:
    #             print(line.decode("utf-8"), flush=True)

    # def stream_data():
    #     for i in range(10):
    #         yield f"数据块 {i}"
    #         time.sleep(0.5)

    # 刷新
    # st.rerun()
