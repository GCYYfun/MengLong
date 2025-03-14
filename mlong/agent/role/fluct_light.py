import json
from mlong.memory.short_term_memory import ShortTermMemory
from mlong.memory.working_memory import WorkingMemory
from mlong.agent.role.role_agent import RoleAgent


class FluctLight(RoleAgent):
    def __init__(
        self,
        role_config: dict = None,
        st_memory_file=None,
        wm_memory_file=None,
        model_id: str = None,
    ):
        super(FluctLight, self).__init__(role_config,model_id)

        if st_memory_file is None:
            st_memory_file = "memory/memcache/short_term_memory.json"
        if wm_memory_file is None:
            wm_memory_file = "memory/memcache/working_memory.json"

        self.st = ShortTermMemory(memory_file=st_memory_file)
        self.wm = WorkingMemory(memory_file=st_memory_file)

    def update_system_prompt(self, message):
        self.role_var.update(message)
        self.role_system = self.role_system_template.substitute(self.role_var)
        self.context_manager.system = self.role_system

    def chat_with_mem(self, input_messages):
        # some_thoughts = self.wm.central_executive(input_messages)
        some_thoughts = self.st.shot_memory()
        self.update_system_prompt({"daily_logs": some_thoughts})

        return self.chat(input_messages=input_messages)

    def chat_stream_with_mem(self, input_messages):
        # some_thoughts = self.wm.central_executive(input_messages)
        some_thoughts = self.st.daily_logs
        self.update_system_prompt({"daily_logs": some_thoughts})

        yield self.chat_stream(input_messages=input_messages)

    def summary(self):
        p = """[对话结束,总结我们的对话,根据时间、地点、人物、事、备注的json格式输出,只关注对话内容，不要包含你个人的背景信息]
        回复的json格式如下:
        {
            时间: str, 
            地点: [str,], 
            人物: [str,], 
            事件: [str,], 
            备注: [str,]
        }
        """
        response = self.chat(input_messages=p)
        self.st.daily_logs.append(response)
        self.st.remember()
        return response

    def reset(self):
        self.chat_man.clear()
        self.st.reset()

    def check_json_format(self, response):
        try:
            json.loads(response)
        except json.JSONDecodeError:
            raise ValueError("回复的json格式错误")
        return True
