from mlong.agent.conversation.conversation_ata import AgentToAgentChat

# role_config1 = {
#     "id": "Alice",
#     "role_system": "你是一个中国${gender}性，你的名字叫${name}。年龄${age}岁。\n\n${topic}\n\n${daily_logs}",
#     "role_info": {
#         "name": "Alice",
#         "gender": "女",
#         "age": "18"
#     },
#     "role_var": {
#         "topic": "",
#         "daily_logs": ""
#     }
# }
# role_config2 = {
#     "id": "Bob",
#     "role_system": """你是一个中国${gender}性，你的名字叫${name}。年龄${age}岁.

#     ${topic}

#     ${daily_logs}
#     """,
#     "role_info": {
#         "name": "Bob",
#         "gender": "男",
#         "age": "20"
#     },
#     "role_var": {
#         "topic": "",
#         "daily_logs": ""
#     }
# }
# topic = {
#     "prompt": """
#     [任务] 与${peer_name}聊天
#         你正在和${peer_name}的闲聊,大约交流5句话,[END]表示自己结束。
#     [背景信息]
#         ${background}
#     [时间]
#         ${time}
#     [地点]
#         ${place}
#     [参与者]
#         ${participants}
# """,
#     "topic_var": {
#         "gender": "女",
#         "name": "Alice",
#         "age": "18"
#     }
# }

# 角色配置
role_config1 = {
    "id": "柳天天",
    "role_system": "你扮演一个${gender}性，名字叫${name}，年龄${age}岁。\n\n${topic}\n\n${daily_logs}",
    "role_info": {"name": "柳天天", "gender": "女", "age": "20"},
    "role_var": {"topic": "", "daily_logs": ""},
}

role_config2 = {
    "id": "叶凡",
    "role_system": "你扮演一个${gender}性，名字叫${name}，年龄${age}岁。\n\n${topic}\n\n${daily_logs}",
    "role_info": {"name": "叶凡", "gender": "男", "age": "25"},
    "role_var": {"topic": "", "daily_logs": ""},
}

# 对话主题模板
topic_template = """
[任务] 与${peer_name}进行符合自己性格与背景的聊天，交互式聊天。
[描述] 你正在和${peer_name}进行自然对话。不一定每句话都要回复。
[规则]
每段对话由两部分组成：
- 对话元信息：描述本次对话的状态。
- 对话内容：描述本次对话的内容。

example:

```对话元信息
- <心情>:(愉悦、悲伤，愤怒，恐惧，惊讶，平静)
- <态度>:(友好、热情、冷淡、中性、恶劣)
- <心里活动>
- <指示符号>
```
<内容>

正常对话指示符号为[NONE]
一方想连续说话则指示符号输出[CONTINUE]
看见对方输出[CONTINUE]后，如果不打算打断则输出[SKIP],打断则输出[BREAK]。
如果一方说完话，另一方无语则另一方输出[PASS]
结束话题使用[END]符号结尾。

互相交流,不要自言自语，等待对方反应，再继续对话，简单聊几句，每人每句最多20个字，然后自然的结束话题。
思考推理要简明扼要，不要长篇大论。抓住重点，不要偏离主题，抓住重点。

[对方信息]
${peer_info}

接下来直接开始对话。中文输出。
"""


ata = AgentToAgentChat(
    active_role=role_config1,
    passive_role=role_config2,
    topic=topic_template,
)

res = ata.chat()
print(res)
