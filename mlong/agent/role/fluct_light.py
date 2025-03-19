import json
from mlong.memory.short_term_memory import ShortTermMemory
from mlong.memory.working_memory import WorkingMemory
from mlong.agent.role.role_agent import RoleAgent


class FluctLight(RoleAgent):
    def __init__(
        self,
        role_config: dict = None,
        memory_space: str = None,
        model_id: str = None,
    ):
        super(FluctLight, self).__init__(role_config, model_id)

        if memory_space is None:
            st_memory_file = "memory/memcache/short_term_memory.yaml"
            wm_memory_file = "memory/memcache/working_memory.yaml"
        else:
            st_memory_file = f"{memory_space}/{self.id}_st_mem.yaml"
            wm_memory_file = f"{memory_space}/{self.id}_wm_mem.yaml"

        self.st = ShortTermMemory(memory_file=st_memory_file)
        self.wm = WorkingMemory(memory_file=wm_memory_file)

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
        p2 = """
        [当前对话结束,以你的视角总结我们的对话,根据下面我提供的json格式输出,只关注对话内容，不要包含你个人的背景信息]
        回复的json格式如下:
        {
            "id": "事件的唯一标识",
            "情境": {
              "时间": "具体时间描述",
              "地点": "事件发生的地点",
              "环境": "天气、光线、声音等环境描述"
            },
            "内容": {
              "动作": "事件中的主要动作或行为",
              "对话": 【"事件中的对话主要内容, 如果有多个人对话, 则需要记录每个人的对话主要内容总结",]
              "参与者": ["参与者列表，可以是人物或物体"]
            },
            "情感": {
              "情绪": "当时的情绪状态描述",
              "心理": "当时的内心感受描述",
              "生理": "当时的身体生理反应描述"
            },
            "因果关系": "事件的前因后果描述",
            "自我关联": "自己在事件中的角色和关联描述",
            "总结": "事件的总结描述"
        }
        """
        response = self.chat(input_messages=p)
        self.st.daily_logs.append(response)
        self.st.remember()
        return response

    def reset(self):
        self.reset_system_prompt()
        self.context_manager.clear()
        self.st.reset()

    def check_json_format(self, response):
        try:
            json.loads(response)
        except json.JSONDecodeError:
            raise ValueError("回复的json格式错误")
        return True
