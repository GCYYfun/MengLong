import json
from mlong.agent.role_play import RoleAgent


role_config = {
    "id": "Alice",
    "role_system": "你是一个中国${gender}性，你的名字叫${name}。\n\n${topic}\n\n${daily_logs}",
    "role_info": {"name": "Alice", "gender": "女", "age": "18"},
    "role_var": {"topic": "", "daily_logs": ""},
}

agent = RoleAgent(role_config)
res = agent.chat_stream("你好")
# {"event": "start:assistant"}
# {"data": "\u4f60\u597d\uff01"}
# {"data": "\u5f88\u9ad8\u5174"}
# {"data": "\u89c1"}
# {"data": "\u5230\u4f60\u3002\u6211"}
# {"data": "\u662fAlice"}
# {"data": "\uff0c"}
# {"data": "\u6709"}
# {"data": "\u4ec0\u4e48\u6211"}
# {"data": "\u80fd\u5e2e\u52a9"}
# {"data": "\u4f60\u7684\u5417"}
# {"data": "\uff1f"}
# {"event": "stop:end_turn"}
for r in res:
    r = json.loads(r)
    match r:
        case {"event": event}:
            print(event, flush=True)
        case {"data": content}:
            print(f"{content}", end="", flush=True)
        case {"reasoning_data": content}:
            print(f"{content}", end="", flush=True)
        case _:
            pass  # 忽略其他情况
