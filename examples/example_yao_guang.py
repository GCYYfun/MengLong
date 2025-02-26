import streamlit as st
import asyncio, json, os, sys, yaml

# 设置项目根目录, 使得可以直接import mlong
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mlong.agent.role_play.yao_guang import YaoGuang

# 设置页面标题
st.set_page_config(page_title="Yao Guang", layout="wide")

st.title("Yao Guang 展示页面")

# 初始化会话状态
if "current_conversation" not in st.session_state:
    st.session_state.current_conversation = []
if "history" not in st.session_state:
    # 改为列表，其中每个元素是一个对话主题（列表形式的消息）
    st.session_state.history = []
if "memory" not in st.session_state:
    st.session_state.memory = []

# 加载角色信息并实例化yg，但保证yg保持状态
if "yg" not in st.session_state:
    with open(
        os.path.join("examples", "example_configs", "linyuqiu.yaml"),
        "r",
        encoding="utf-8",
    ) as f:
        role_info = yaml.safe_load(f)
    st.session_state.yg = YaoGuang(
        role_info=role_info,
        st_memory_file=os.path.join("examples", "example_configs", "yaogunag_st.json"),
        wm_memory_file=os.path.join("examples", "example_configs", "yaogunag_wm.json"),
    )

yg = st.session_state.yg

# 展示区
st.markdown("<h3 style='text-align: center;'>当前对话</h3>", unsafe_allow_html=True)

# 用一个 placeholder 来显示整个对话窗口
conv_placeholder = st.empty()


def draw_conversation():
    conversation_html = ""
    for msg in st.session_state.current_conversation:
        if msg.get("role") == "system":
            conversation_html += f"<div style='text-align: center; background-color:#111; padding:5px; border: 2px solid red;border-radius: 5px;'>{msg.get('content', '')}</div><br>"
        elif msg.get("role") == "user":
            conversation_html += f"<div style='text-align: left; color: blue; border:1px solid #CCC; padding:5px; border-radius:5px; margin:5px;'>用户: {msg.get('content', '')}</div><br>"
        elif msg.get("role") == "assistant":
            conversation_html += f"<div style='text-align: right; color: green; border:1px solid #CCC; padding:5px; border-radius:5px; margin:5px;'>助手: {msg.get('content', '')}</div><br>"
    conv_placeholder.markdown(conversation_html, unsafe_allow_html=True)


# 初始绘制当前对话
draw_conversation()

# Row 2: 修改历史对话管理为折叠列表，每个历史对话为一个话题
cols = st.columns(2)
with cols[0]:
    st.subheader("历史对话管理")
    with st.container(border=True):
        history_placeholder = st.empty()
        if st.session_state.history:
            for index, topic in enumerate(st.session_state.history, 1):
                with st.expander(f"话题 {index}", expanded=False):
                    for msg in topic:
                        role = msg.get("role", "未知")
                        content = msg.get("content", "")
                        if role == "system":
                            st.info(content)
                        elif role == "user":
                            st.markdown(
                                f"<div style='text-align: left; color: blue;'>用户: {content}</div>",
                                unsafe_allow_html=True,
                            )
                        elif role == "assistant":
                            st.markdown(
                                f"<div style='text-align: right; color: green;'>助手: {content}</div>",
                                unsafe_allow_html=True,
                            )
        else:
            st.write("暂无历史话题")
with cols[1]:
    st.subheader("记忆管理")
    with st.container(border=True):
        memory_placeholder = st.empty()
        if st.session_state.memory:
            for i, record in enumerate(st.session_state.memory, start=1):
                with st.expander(f"记忆记录 {i}", expanded=False):
                    st.markdown("**JSON 格式:**")
                    try:
                        parsed = json.loads(record)
                        st.json(parsed)
                    except Exception:
                        st.json({"text": record})
        else:
            st.write("暂无记忆记录")


# 彩虹分割线
st.markdown(
    '<hr style="border:0; height:4px; background: linear-gradient(to right, red, orange, yellow, green, blue, indigo, violet)">',
    unsafe_allow_html=True,
)


# 定义模型流式响应的异步生成器
async def event_generator(bot_response):
    current_response = ""
    for item in bot_response:
        try:
            parsed = json.loads(item)
            if "data" in parsed:
                text_piece = parsed["data"]
                current_response += text_piece
            elif "event" in parsed:
                event_info = parsed["event"]
                current_response += f"[{event_info}]"
        except Exception as e:
            current_response += item
        # 更新当前会话中最后一条助手消息
        st.session_state.current_conversation[-1]["content"] = current_response
        draw_conversation()
        await asyncio.sleep(0)


# 功能区

# 使用 st.chat_input 获取用户输入
user_input = st.chat_input("请输入信息", key="chat_input")

# 处理用户输入
if user_input:
    # 如果对话为空，检查并添加 system 信息（仅添加一次）
    if not st.session_state.current_conversation:
        role_system = yg.system_prompt.strip() if hasattr(yg, "system_prompt") else ""
        if role_system:
            st.session_state.current_conversation.append(
                {"role": "system", "content": role_system}
            )

    # 确保上一个消息为助手回复，或者对话为空 或 system 消息
    if (not st.session_state.current_conversation) or (
        st.session_state.current_conversation[-1].get("role") in ["assistant", "system"]
        and st.session_state.current_conversation[-1].get("content") != ""
    ):
        # 添加用户消息
        st.session_state.current_conversation.append(
            {"role": "user", "content": user_input}
        )
        # 添加助手空占位消息
        st.session_state.current_conversation.append(
            {"role": "assistant", "content": ""}
        )
        draw_conversation()
        # 准备传给模型的格式化输入，可根据需求调整
        format_input = f"{user_input}"
        print("context len", len(yg.chat_man.messages))
        bot_response = yg.chat_stream_with_mem(format_input)
        asyncio.run(event_generator(bot_response))
        st.rerun()
    else:
        st.warning("请等待助手回复后再发送消息")

# 显示两个按钮：清空当前 和 重置全部
col_clear, col_reset = st.columns(2, gap="large")
with col_clear:
    if st.button("清空当前"):
        if st.session_state.current_conversation:
            st.session_state.history.append(
                st.session_state.current_conversation.copy()
            )
            st.session_state.current_conversation = []
            st.session_state.memory.append(yg.summary())
            yg.chat_man.clear()
        st.rerun()
with col_reset:
    if st.button("重置全部"):
        st.session_state.current_conversation = []
        st.session_state.history = []
        st.session_state.memory = []
        yg.reset()
        st.rerun()


# ...可以添加更多功能实现...
