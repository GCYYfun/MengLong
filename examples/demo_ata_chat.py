from mlong.agent.conversation.chat_ata import AgentToAgentChat

role_config1 = {
    "role_system": "你是一个中国${gender}性，你的名字叫${name}。年龄${age}岁。\n\n${topic}\n\n${daily_logs}",
    "role_info": {
        "name": "Alice",
        "gender": "女",
        "age": "18"
    },
    "role_var": {
        "topic": "",
        "daily_logs": ""
    }
}
role_config2 = {
    "role_system": "你是一个中国${gender}性，你的名字叫${name}。年龄${age}岁\n\n${topic}\n\n${daily_logs}",
    "role_info": {
        "name": "Bob",
        "gender": "男",
        "age": "20"
    },
    "role_var": {
        "topic": "",
        "daily_logs": ""
    }
}
topic = """
[任务] 与${peer_name}聊天
你正在和${peer_name}的闲聊,大约交流5句话,[END]表示自己结束。
[已知的背景信息]
${peer_info}
"""

ata = AgentToAgentChat(active_role=role_config1, passive_role=role_config2, topic=topic)

res = ata.chat()
print(res)