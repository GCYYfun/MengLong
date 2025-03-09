import json
import re
import time
import streamlit as st
from streamlit import chat_message
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from mlong.agent.conversation.chat_ata import AgentToAgentChat

# 角色配置
role_config1 = {
    "id":"Alice",
    "role_system": "你是一个中国${gender}性，名字叫${name}，年龄${age}岁。\n\n${topic}\n\n${daily_logs}",
    "role_info": {"name": "Alice", "gender": "女", "age": "18"},
    "role_var": {"topic": "", "daily_logs": ""}
}

role_config2 = {
    "id":"Bob",
    "role_system": "你是一个中国${gender}性，名字叫${name}，年龄${age}岁。\n\n${topic}\n\n${daily_logs}",
    "role_info": {"name": "Bob", "gender": "男", "age": "25"},
    "role_var": {"topic": "", "daily_logs": ""}
}

# 对话主题模板
topic_template = """
[任务] 与${peer_name}进行符合自己性格与背景的聊天
[描述] 你正在和${peer_name}进行自然对话。不必一定回复每句话。
[规则]
每段对话由两部分组成：
- 对话元信息：描述本次对话的状态。
- 对话内容：描述本次对话的内容。

example:
#### 对话元信息
- <心情>:(愉悦、悲伤，愤怒，恐惧，惊讶，平静)
- <态度>:(友好、热情、冷淡、中性、恶劣)
- <心里活动>
- <指示符号>
#### 对话内容
<内容>

正常对话指示符号为[NONE]
一方想连续说话则指示符号输出[CONTINUE]
看见对方输出[CONTINUE]后，如果不打算打断则输出[SKIP],打断则输出[BREAK]。
如果一方说完话，另一方无语则另一方输出[PASS]
结束话题使用[END]符号结尾。

交流大概5-8句话，然后自然的结束话题。

[对方信息]
${peer_info}

接下来直接开始对话。
"""

# 初始化Streamlit界面
st.set_page_config(page_title="AI角色对话剧场", page_icon="🎭", layout="wide")
st.title("🎭 双AI角色情景对话")

# CSS样式定制
st.markdown("""
<style>
.chat-container {
    border-radius: 15px;
    padding: 2rem;
    background-color: #f8f9fa;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.avatar {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    object-fit: cover;
    margin-right: 1rem;
}

.chat-bubble {
    padding: 1rem;
    border-radius: 15px;
    margin: 0.5rem 0;
    max-width: 80%;
    position: relative;
}

.ai1-bubble {
    background: #e3f2fd;
    margin-left: 70px;
}

.ai2-bubble {
    background: #fce4ec;
    margin-right: 70px;
}
</style>
""", unsafe_allow_html=True)

# 初始化会话状态
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'ata' not in st.session_state:
    st.session_state.ata = AgentToAgentChat(
        active_role=role_config1,
        passive_role=role_config2,
        topic=topic_template
    )

# 创建两栏布局
col1, col2 = st.columns([1, 1], gap="large")

# 对话控制按钮
if st.button('🚀 开始对话', use_container_width=True, key='start_chat'):
    st.session_state.conversation = []
    st.session_state.disabled = True
    with st.spinner('角色正在准备中...'):
        full_response = ""
        placeholder = st.empty()
        
        # [Stream Processing 流式处理]
        # 实时处理对话引擎的事件流，包含两种数据类型：
        # 1. 事件类型：标记对话开始/结束
        # 2. 数据块：实际对话内容
        # Real-time processing of chat event stream containing:
        # 1. Events: Mark start/end of turns
        # 2. Data chunks: Actual conversation content
        for chunk in st.session_state.ata.chat_stream():
            try:
                data = json.loads(chunk)
                
                # [Event Handling 事件处理]
                # 识别事件类型并设置当前说话者
                # Identifies event type and sets current speaker
                if "event" in data:
                    event_type = data["event"].split(":")[0]
                    if event_type == "start":
                        current_speaker = "Alice" if "Alice" in data["event"] else "Bob"
                        st.session_state.conversation.append({"role": current_speaker, "content": ""})
                    elif event_type == "stop":
                        break
                
                # [Content Processing 内容处理]
                # 将数据块追加到当前说话者的对话记录
                # Appends data chunks to current speaker's conversation
                if "data" in data:
                    if st.session_state.conversation:
                        st.session_state.conversation[-1]["content"] += data["data"]
                        
                        # 实时更新界面
                        with placeholder.container():
                            # for msg in st.session_state.conversation:
                            with chat_message(name=st.session_state.conversation[-1]["role"], avatar="user" if st.session_state.conversation[-1]["role"] == "Alice" else "assistant"):
                                st.markdown(st.session_state.conversation[-1]["content"])
            
            except json.JSONDecodeError:
                pass

# 显示完整对话历史
with st.expander("📜 完整对话记录"):
    for msg in st.session_state.conversation:
        st.markdown(f"**{msg['role']}**: {msg['content']}")