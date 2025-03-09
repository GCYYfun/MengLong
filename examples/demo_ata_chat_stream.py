import json
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
[CONTINUE]: CONTINUE方继续，另一方等待
[SKIP]: SKIP方跳过，另一方继续
结束话题使用[END]符号结尾。

交流大概5-8句话，然后自然的结束话题。

[对方信息]
${peer_info}

接下来直接开始对话。
"""

# 初始化双角色对话
ata = AgentToAgentChat(
    active_role=role_config1,
    passive_role=role_config2,
    topic=topic_template
)

# 流式对话处理
current_speaker = ""
current_message = ""
for chunk in ata.chat_stream():
    try:
        data = json.loads(chunk)
        
        # 处理事件类型
        if "event" in data:
            event_type = data["event"].split(":")[0]
            if event_type == "start":
                current_speaker = "Alice" if "Alice" in data["event"] else "Bob"
                print(f"\n\n{current_speaker}: ", end="", flush=True)
            # elif event_type == "stop":
            #     if "[END]" in current_message:
            #         break
        
        # 处理对话内容
        if "data" in data:
            content = data["data"]
            current_message += content
            print(content, end="", flush=True)
            
    except json.JSONDecodeError:
        pass

print("\n\n对话结束")