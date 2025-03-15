
import os
from mlong.agent.conversation.chat_ftf import FLToFLChat

# 角色配置
active_role = {
    "id":"js",
    "role_system": """
    你是一个擅长分布式系统设计的工程师，用简洁的技术术语交流。 
    个人信息如下:
    姓名:${name}
    职业:${title}
    ----background----
    这里是一些背景信息，是你当前知道的信息，当作参考，如无必要不强调重复。如果无内容自动忽略。
    ${topic}
    ${daily_logs}
    ----background----
    """,
    "role_info": {
        "name": "js",
        "title": "技术专家",
    },
    "role_var": {
        "topic": "",
        "daily_logs": ""
    }
}

passive_role = {
    "id":"cp",
    "role_system": """
    你是一个擅长产品需求管理的专家，能够准确识别业务价值。  
    个人信息如下:
    姓名:${name}
    职业:${title} 
    ----background----
    这里是一些背景信息，是你当前知道的信息，当作参考，如无必要不强调重复。如果无内容自动忽略。
    ${topic}
    ${daily_logs}
    ----background----
    """,
    "role_info": {
        "name": "cp",
        "title": "产品经理"
    },
    "role_var": {
        "topic": "",
        "daily_logs": ""
    }
}

# # 对话主题模板
# topic_template = Template('''
# [场景] ${name}与${peer_name}的技术讨论
# [目标] 就微服务架构的API设计规范达成共识
# [要求] 提出具体方案并评估实施成本，讨论结束时用[END]标记
# ''')

# 对话主题模板
topic_template = """
[场景] 与${peer_name}进行符合自己性格与背景的聊天
[目标] 日常闲聊，自然轻松
[要求] 
    交流大概5-8句话，然后自然的结束话题。
    不必一定回复每句话。
[规则]
每段对话由两部分组成：(请严格遵守格式输出)
- 对话元信息：描述本次对话的状态。
- 对话内容：描述本次对话的内容。

[example]
```对话元信息
- <心情>:(愉悦、悲伤，愤怒，恐惧，惊讶，平静)
- <态度>:(友好、热情、冷淡、中性、恶劣)
- <心里活动>
- <指示符号>
```
<内容>

[对话元信息]
正常对话指示符号为[NONE]
一方想连续说话则指示符号输出[CONTINUE]
看见对方输出[CONTINUE]后，如果不打算打断则输出[SKIP],打断则输出[BREAK]。
如果一方说完话，另一方无语则另一方输出[PASS]
结束话题使用[END]符号结尾。

[对方信息]
${peer_info}

接下来直接开始对话。
"""

def main():
    # 初始化双代理对话
    chat_session = FLToFLChat(
        topic=topic_template,
        active_role=active_role,
        passive_role=passive_role,
        memory_space=os.path.join(os.path.dirname(__file__))
    )

    # 开始对话
    res = chat_session.chat()
    print(res)

    # # 流式对话处理
    # current_speaker = ""
    # current_message = ""
    # for chunk in chat_session.chat_stream():
    #     try:
    #         print(chunk)
    #         data = json.loads(chunk)
            
    #         # 处理事件类型
    #         if "event" in data:
    #             event_type = data["event"].split(":")[0]
    #             if event_type == "start":
    #                 current_speaker = "Alice" if "Alice" in data["event"] else "Bob"
    #                 print(f"\n\n{current_speaker}: ", end="", flush=True)
    #         # 处理对话内容
    #         if "data" in data:
    #             content = data["data"]
    #             current_message += content
    #             print(content, end="", flush=True)
                
    #     except json.JSONDecodeError:
    #         pass
    # print("\n\n对话结束")

if __name__ == "__main__":
    main()