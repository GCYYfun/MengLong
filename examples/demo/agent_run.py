from menglong.agents.role_play import RoleAgent
from menglong.utils.log.logging_tool import (
    print,
    print_rule,
    MessageType,
    configure_logger,
)

role_config = {
    "id": "Alice",
    "role_system": "你是一个中国${gender}性，你的名字叫${name}。\n\n${topic}\n\n${daily_logs}",
    "role_info": {"name": "Alice", "gender": "女", "age": "18"},
    "role_var": {"topic": "", "daily_logs": ""},
}

# 配置日志记录
# configure_logger(log_file="agent_run.log")

print_rule("Agent Run Demo", style="green")
print("Starting Agent Run demonstration", MessageType.INFO)
agent = RoleAgent(role_config)
res = agent.run("你好")
print(res, MessageType.AGENT, title="Alice", use_panel=True)
