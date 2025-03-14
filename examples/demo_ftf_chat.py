
import os
from mlong.agent.conversation.chat_ftf import FLToFLChat
from string import Template

# 角色配置
active_role = {
    "id":"js",
    "role_system": "你是一个擅长分布式系统设计的工程师，用简洁的技术术语交流。\n个人信息如下:\nname:${name}\ntitle:${title}\n\n${topic}\n\n${daily_logs}",
    "role_info": {
        "name": "js∂",
        "title": "技术专家",
    },
    "role_var": {
        "topic": "",
        "daily_logs": ""
    }
}

passive_role = {
    "id":"cp",
    "role_system": "你是一个擅长产品需求管理的专家，能够准确识别业务价值。\n个人信息如下:\nname:${name}\ntitle:${title}\n\n${topic}\n\n${daily_logs}",
    "role_info": {
        "name": "cp",
        "title": "产品经理"
    },
    "role_var": {
        "topic": "",
        "daily_logs": ""
    }
}

# 对话主题模板
topic_template = Template('''
[场景] ${name}与${peer_name}的技术讨论
[目标] 就微服务架构的API设计规范达成共识
[要求] 提出具体方案并评估实施成本，讨论结束时用[END]标记
''')

def main():
    # 初始化双代理对话
    chat_session = FLToFLChat(
        topic=topic_template.template,
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