from mlong.agent.role import RoleAgent
from mlong.model_interface.utils import user

role_config = {
    "role_system": "你是一个中国${gender}性，你的名字叫${name}。\n\n${topic}\n\n%{daily_logs}",
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

agent = RoleAgent(role_config)
res = agent.chat("你好")
print(res)
