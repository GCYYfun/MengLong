import os
import sys
import yaml
import streamlit as st

# 将项目根目录添加到路径中
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mlong.agent.role import FluctLight

# 确保configs目录存在
configs_dir = os.path.join(os.path.dirname(__file__), "configs")
if not os.path.exists(configs_dir):
    os.makedirs(configs_dir)

# 页面配置
st.set_page_config(
    page_title="FluctLight 演示",
    page_icon="🤖",
    layout="wide"
)

# 应用全局样式 - 全面覆盖Streamlit默认样式
st.markdown("""
<style>
/* ===== 全局样式与重置 ===== */
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap');

* {
    font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
}

.main .block-container {
    padding: 2rem 3rem !important;
    max-width: 1200px;
    background-color: #000000;
}

/* ===== 自定义滚动条 ===== */
::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}

::-webkit-scrollbar-track {
    background: #333333;
    border-radius: 5px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(45deg, #00FF00, #00CC00);
    border-radius: 5px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(45deg, #009900, #006600);
}

/* ===== 标题与文本 ===== */
h1, h2, h3, h4, h5, h6 {
    font-weight: 700 !important;
    color: #FFFFFF !important;
}

h1 {
    background: linear-gradient(90deg, #00FF00 0%, #00CC00 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.5rem !important;
    margin-bottom: 1rem !important;
    padding-bottom: 0.5rem !important;
    border-bottom: 1px solid rgba(0, 255, 0, 0.1);
}

h2 {
    color: #AAAAAA !important;
    font-size: 1.8rem !important;
    margin-top: 1.5rem !important;
}

p, li, div {
    color: #AAAAAA;
    line-height: 1.6 !important;
}

/* ===== 侧边栏样式 ===== */
.css-1544g2n {
    background: linear-gradient(180deg, #111111 0%, #222222 100%) !important;
    border-right: 1px solid rgba(0, 255, 0, 0.1) !important;
}

.css-1544g2n .sidebar-content {
    padding: 2rem 1rem !important;
}

[data-testid="stSidebar"] {
    background-image: linear-gradient(180deg, rgba(0, 255, 0, 0.05) 0%, rgba(0, 255, 0, 0.05) 100%);
    box-shadow: 1px 0 10px rgba(0, 0, 0, 0.05);
}

[data-testid="stSidebarNav"] {
    padding-top: 2rem !important;
}

[data-testid="stSidebarNav"] a {
    margin-bottom: 0.5rem !important;
    padding: 0.5rem 1rem !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}

[data-testid="stSidebarNav"] a:hover {
    background-color: rgba(0, 255, 0, 0.1) !important;
}

/* ===== 表单与输入元素 ===== */
/* 输入框 */
.stTextInput input, .stNumberInput input, div.stTextArea textarea {
    padding: 0.75rem 1rem !important;
    font-size: 1rem !important;
    border-radius: 8px !important;
    border: 1px solid #333333 !important;
    background-color: #222222 !important;
    color: #FFFFFF !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.02) !important;
    transition: all 0.3s ease !important;
}

.stTextInput input:focus, .stNumberInput input:focus, div.stTextArea textarea:focus {
    border-color: #00FF00 !important;
    box-shadow: 0 0 0 3px rgba(0, 255, 0, 0.1) !important;
}

.stTextArea div[data-baseweb="textarea"] {
    background-color: #222222 !important;
}

/* ===== 现代化下拉菜单 ===== */
/* 下拉菜单容器样式 */
div[data-baseweb="select"] {
    border-radius: 12px !important;
    border: none !important;
    box-shadow: 0 2px 8px rgba(0, 255, 0, 0.04) !important;
    transition: all 0.3s ease !important;
}

/* 下拉菜单触发器样式 */
div[data-baseweb="select"] > div:first-child {
    background: #222222 !important;
    border-radius: 10px !important;
    border: 1px solid rgba(0, 255, 0, 0.1) !important;
    padding: 0.5rem !important;
    min-height: 40px !important;
    display: flex !important;
    align-items: center !important;
    transition: all 0.3s ease !important;
    color: #FFFFFF !important;
}

div[data-baseweb="select"] > div:first-child:hover {
    border-color: rgba(0, 255, 0, 0.3) !important;
    box-shadow: 0 2px 10px rgba(0, 255, 0, 0.1) !important;
}

div[data-baseweb="select"]:focus-within > div:first-child {
    border-color: #00FF00 !important;
    box-shadow: 0 0 0 2px rgba(0, 255, 0, 0.15) !important;
}

/* 下拉箭头样式 */
div[data-baseweb="select"] svg {
    color: #00FF00 !important;
    transition: transform 0.2s ease;
}

div[data-baseweb="select"]:focus-within svg {
    transform: rotate(180deg);
}

/* 下拉菜单下拉内容样式 */
div[role="listbox"] {
    background: #222222 !important;
    border-radius: 10px !important;
    border: 1px solid rgba(0, 255, 0, 0.1) !important;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2) !important;
    margin-top: 8px !important;
    overflow: hidden !important;
    z-index: 999 !important;
    padding: 0.5rem !important;
    animation: fadeInDown 0.2s ease-out !important;
}

@keyframes fadeInDown {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* 下拉选项样式 */
div[role="option"] {
    border-radius: 8px !important;
    padding: 0.75rem 1rem !important;
    margin: 0.2rem 0 !important;
    transition: all 0.2s ease !important;
    color: #FFFFFF !important;
}

div[role="option"]:hover {
    background-color: rgba(0, 255, 0, 0.08) !important;
    cursor: pointer !important;
}

div[aria-selected="true"] {
    background: linear-gradient(90deg, rgba(0, 255, 0, 0.1), rgba(0, 204, 0, 0.1)) !important;
    color: #00FF00 !important;
    font-weight: 500 !important;
    position: relative !important;
}

div[aria-selected="true"]::before {
    content: "✓";
    position: absolute;
    right: 1rem;
    color: #00FF00;
    font-weight: bold;
}

/* 选项分隔线 */
div[data-baseweb="menu"] hr {
    margin: 0.5rem 0 !important;
    border: none !important;
    height: 1px !important;
    background: rgba(0, 255, 0, 0.1) !important;
}

/* 无选项状态 */
div[data-baseweb="menu"] div[role="alert"] {
    padding: 1rem !important;
    color: #AAAAAA !important;
    text-align: center !important;
    font-style: italic !important;
}

/* ===== 按钮 ===== */
.stButton button, button.css-a29d8k, button.css-1cpxqw2 {
    padding: 0.5rem 1.2rem !important;
    background: linear-gradient(90deg, #00FF00 0%, #00CC00 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    letter-spacing: 0.5px !important;
    text-transform: none !important;
    box-shadow: 0 2px 5px rgba(0, 204, 0, 0.2) !important;
    transition: all 0.3s ease !important;
}

.stButton button:hover, button.css-a29d8k:hover, button.css-1cpxqw2:hover {
    background: linear-gradient(90deg, #009900 0%, #006600 100%) !important;
    box-shadow: 0 4px 10px rgba(0, 204, 0, 0.3) !important;
    transform: translateY(-2px) !important;
}

.stButton button:active, button.css-a29d8k:active, button.css-1cpxqw2:active {
    transform: translateY(0) !important;
    box-shadow: 0 1px 3px rgba(0, 204, 0, 0.3) !important;
}

/* ===== 表单容器 ===== */
.stForm {
    border: 1px solid rgba(0, 255, 0, 0.1) !important;
    padding: 1.5rem !important;
    border-radius: 12px !important;
    background-color: #111111 !important;
    box-shadow: 0 3px 15px rgba(0, 0, 0, 0.05) !important;
    margin-bottom: 2rem !important;
}

/* ===== 展开器/折叠面板 ===== */
.streamlit-expanderHeader {
    font-size: 1rem !important;
    color: #00FF00 !important;
    background-color: rgba(0, 255, 0, 0.05) !important;
    border-radius: 8px !important;
    padding: 0.75rem 1rem !important;
}

.streamlit-expanderHeader:hover {
    background-color: rgba(0, 255, 0, 0.08) !important;
}

.streamlit-expanderContent {
    background-color: #111111 !important;
    border-radius: 0 0 8px 8px !important;
    padding: 1rem !important;
    border: 1px solid rgba(0, 255, 0, 0.1) !important;
    border-top: none !important;
}

/* ===== 聊天消息样式 ===== */
.chat-message {
    padding: 1.5rem; 
    border-radius: 1rem; 
    margin-bottom: 1.2rem; 
    display: flex;
    flex-direction: column;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    border: 1px solid rgba(0,0,0,0.05);
    transition: all 0.3s ease;
    position: relative;
}

.chat-message:hover {
    box-shadow: 0 4px 10px rgba(0,0,0,0.08);
}

/* 用户消息样式 */
.chat-message.user {
    background: linear-gradient(135deg, rgba(255, 239, 186, 0.5) 0%, rgba(255, 255, 255, 0.95) 100%);
    border-right: 3px solid #ffcc00;
    margin-left: 2rem;
    margin-right: 0.5rem;
}

.chat-message.user::before {
    content: '';
    position: absolute;
    left: -12px;
    top: 20px;
    width: 20px;
    height: 20px;
    background: linear-gradient(135deg, rgba(255, 239, 186, 0.5) 0%, rgba(255, 255, 255, 0.95) 100%);
    transform: rotate(45deg);
    border-radius: 3px;
    border-left: 1px solid rgba(0,0,0,0.05);
    border-bottom: 1px solid rgba(0,0,0,0.05);
}

/* 助手消息样式 */
.chat-message.assistant {
    background: linear-gradient(135deg, rgba(224, 247, 250, 0.5) 0%, rgba(255, 255, 255, 0.95) 100%);
    border-left: 3px solid #00FF00;
    margin-right: 2rem;
    margin-left: 0.5rem;
}

.chat-message.assistant::before {
    content: '';
    position: absolute;
    right: -12px;
    top: 20px;
    width: 20px;
    height: 20px;
    background: linear-gradient(135deg, rgba(224, 247, 250, 0.5) 0%, rgba(255, 255, 255, 0.95) 100%);
    transform: rotate(45deg);
    border-radius: 3px;
    border-right: 1px solid rgba(0,0,0,0.05);
    border-top: 1px solid rgba(0,0,0,0.05);
}

.chat-message .message {
    margin-top: 0.5rem;
    line-height: 1.7;
    font-size: 1.05rem;
}

/* 聊天名称加粗样式 */
.chat-message strong {
    font-size: 1.1rem;
    color: #333;
}

.chat-message.user strong {
    color: #d9a400;
}

.chat-message.assistant strong {
    color: #00FF00;
}

/* ===== 系统信息样式 ===== */
.system-info {
    background: linear-gradient(to right, #111111 0%, #222222 100%);
    padding: 1rem;
    border-radius: 0.8rem;
    margin-bottom: 1rem;
    font-size: 0.85rem;
    border-left: 3px solid #00FF00;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

/* ===== 代码块样式 ===== */
.stCodeBlock, div.stCodeBlock > div {
    border-radius: 8px !important;
}

.stCodeBlock pre {
    background: linear-gradient(45deg, #1e1e2e, #2d2b55) !important;
    padding: 1.2rem !important;
}

.stCodeBlock code {
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace !important;
}

/* ===== 分隔线 ===== */
hr {
    margin: 2rem 0 !important;
    border: none !important;
    height: 1px !important;
    background: linear-gradient(to right, transparent, rgba(0, 255, 0, 0.3), transparent) !important;
}

/* ===== 动画效果 ===== */
@keyframes gradientShift {
    0% {
        background-position: 0% 50%;
    }
    50% {
        background-position: 100% 50%;
    }
    100% {
        background-position: 0% 50%;
    }
}

.stApp::before {
    content: "";
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 5px;
    background: linear-gradient(90deg, #00FF00, #00CC00, #00FF00);
    background-size: 200% 200%;
    animation: gradientShift 4s ease infinite;
    z-index: 999;
}

/* ===== 媒体查询 ===== */
@media screen and (max-width: 768px) {
    .main .block-container {
        padding: 1rem !important;
    }
    
    .chat-message {
        padding: 1rem;
        margin-left: 0.5rem !important;
        margin-right: 0.5rem !important;
    }
}

/* ===== 页脚 ===== */
.footer {
    text-align: center;
    margin-top: 3rem;
    color: #666;
    font-size: 0.9rem;
}
.footer-separator {
    margin: 0 10px;
    color: #ddd;
}
.subtitle {
    font-size: 1.1rem;
    margin-bottom: 2rem;
    color: #666;
}

/* 适配深色模式的下拉菜单 */
@media (prefers-color-scheme: dark) {
    div[data-baseweb="select"] > div:first-child {
        background: #2d2b55 !important;
        border-color: rgba(106, 17, 203, 0.3) !important;
        color: #e0e0e0 !important;
    }
    
    div[role="listbox"] {
        background: #2d2b55 !important;
        border-color: rgba(106, 17, 203, 0.3) !important;
    }
    
    div[role="option"] {
        color: #e0e0e0 !important;
    }
    
    div[role="option"]:hover {
        background-color: rgba(106, 17, 203, 0.2) !important;
    }
    
    div[aria-selected="true"] {
        background: linear-gradient(90deg, rgba(106, 17, 203, 0.2), rgba(37, 117, 252, 0.2)) !important;
    }
}

</style>
""", unsafe_allow_html=True)

# 标题
st.title("✨ FluctLight 智能对话系统")
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
<p class="subtitle">
    <i class="fas fa-brain"></i> 基于记忆的智能角色 | 
    <i class="fas fa-comments"></i> 自然流畅的对话 | 
    <i class="fas fa-lightbulb"></i> 个性化体验
</p>
""", unsafe_allow_html=True)

# 侧边栏 - 角色配置
with st.sidebar:
    st.header("⚙️ 角色设置")
    
    name = st.text_input("名字", "Alice")
    gender = st.selectbox("性别", ["女", "男"])
    age = st.text_input("年龄", "18")
    
    topic = st.text_area("主题设定", "", height=150)
    
    if st.button("应用设置"):
        # 重新配置角色
        st.session_state.role_config = {
            "id": name,
            "role_system": f"你是一个中国${gender}性，你的名字叫${name}。\n\n${topic}\n\n${daily_logs}",
            "role_info": {"name": name, "gender": gender, "age": age},
            "role_var": {"topic": topic, "daily_logs": ""},
        }
        # 重新初始化 FluctLight
        st.session_state.fluctlight = FluctLight(
            role_config=st.session_state.role_config,
            st_memory_file=os.path.join(configs_dir, "fl_st.yaml"),
            wm_memory_file=os.path.join(configs_dir, "fl_wm.yaml"),
        )
        st.session_state.messages = []
        st.success("角色设置已更新！")
    
    st.markdown("---")
    
    st.subheader("🧠 记忆管理")
    
    if st.button("生成对话摘要"):
        summary = st.session_state.fluctlight.summary()
        st.code(summary, language="json")
    
    if st.button("清除记忆"):
        st.session_state.fluctlight.reset()
        st.session_state.messages = []
        st.success("记忆已清除！")

# 初始化会话状态
if 'role_config' not in st.session_state:
    st.session_state.role_config = {
        "id": "Alice",
        "role_system": "你是一个中国${gender}性，你的名字叫${name}。\n\n${topic}\n\n${daily_logs}",
        "role_info": {"name": "Alice", "gender": "女", "age": "18"},
        "role_var": {"topic": "", "daily_logs": ""},
    }

if 'fluctlight' not in st.session_state:
    st.session_state.fluctlight = FluctLight(
        role_config=st.session_state.role_config,
        memory_space=configs_dir
    )

if 'messages' not in st.session_state:
    st.session_state.messages = []

# 显示系统提示信息
with st.expander("系统提示（点击展开查看）"):
    st.code(st.session_state.fluctlight.system_prompt, language="markdown")

# 显示聊天记录
for message in st.session_state.messages:
    with st.container():
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user">
                <div><strong><i class="fas fa-user-circle"></i> 你:</strong></div>
                <div class="message">{message["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant">
                <div><strong><i class="fas fa-robot"></i> {st.session_state.role_config["role_info"]["name"]}:</strong></div>
                <div class="message">{message["content"]}</div>
            </div>
            """, unsafe_allow_html=True)

# 使用表单处理输入 
with st.form("message_form", clear_on_submit=True):
    # 创建一个简单的两列布局
    c1, c2 = st.columns([7, 1])
    
    with c1:
        # 直接放置输入框，不添加任何修饰
        user_input = st.text_input(
            label="",
            placeholder="请输入消息：",
            label_visibility="collapsed", # 隐藏标签
            key="user_input"
        )
        
    with c2:
        # 按钮
        submit = st.form_submit_button("发送", use_container_width=True)
    
    # 处理提交
    if submit and user_input:
        # 添加用户消息到聊天记录
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # 获取 FluctLight 回复
        fl_response = st.session_state.fluctlight.chat_with_mem(user_input)
        
        # 添加助手回复到聊天记录
        st.session_state.messages.append({"role": "assistant", "content": fl_response})
        
        # 显示系统提示更新
        with st.expander("系统提示已更新（点击展开查看）"):
            st.code(st.session_state.fluctlight.system_prompt, language="markdown")
        
        # 重新加载页面以显示新消息
        st.rerun()

# 页脚
st.markdown("---")
st.markdown("""
<div class="footer">
    <p>
        <i class="fas fa-code"></i> FluctLight 智能对话系统 
        <span class="footer-separator">|</span> 
        <i class="fas fa-bolt"></i> 基于Streamlit构建 
        <span class="footer-separator">|</span> 
        <i class="fas fa-heart"></i> 2025
    </p>
</div>
""", unsafe_allow_html=True)