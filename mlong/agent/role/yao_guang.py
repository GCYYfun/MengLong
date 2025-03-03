import json
from mlong.memory.short_term_memory import ShortTermMemory
from mlong.memory.working_memory import WorkingMemory
from mlong.model import Model
from mlong.agent.role_play.role_play_agent import RolePlayAgent


class YaoGuang(RolePlayAgent):
    def __init__(
        self,
        model: Model = None,
        role_info: dict = None,
        st_memory_file=None,
        wm_memory_file=None,
    ):
        super(YaoGuang, self).__init__(model, role_info)

        if st_memory_file is None:
            st_memory_file = "memory/memcache/short_term_memory.json"
        if wm_memory_file is None:
            wm_memory_file = "memory/memcache/working_memory.json"

        self.st = ShortTermMemory(memory_file=st_memory_file)
        self.wm = WorkingMemory(memory_file=st_memory_file)

        # YaoG
        # 我是谁
        # 我在那
        # 我要干什么

        # 记忆

    def chat_with_mem(self, input_messages):
        # some_thoughts = self.wm.central_executive(input_messages)
        some_thoughts = self.st.shot_memory()
        self.update_system_prompt({"daily_logs": some_thoughts})

        # 处理消息
        self.chat_man.add_user_message(input_messages)

        messages = self.chat_man.messages

        res = self.model.chat(messages=messages)

        r = res.choices[0].message.content
        self.chat_man.add_assistant_response(r)

        return r

    def chat_stream_with_mem(self, input_messages):
        # some_thoughts = self.wm.central_executive(input_messages)
        some_thoughts = self.st.daily_logs
        self.update_system_prompt({"daily_logs": some_thoughts})

        reasoning_cache_message = []
        cache_message = []
        self.chat_man.add_user_message(input_messages)

        messages = self.chat_man.messages

        response = self.model.chat(messages=messages, stream=True)
        if response.stream:
            for event in response.stream:
                if "contentBlockDelta" in event:
                    delta = event["contentBlockDelta"]["delta"]
                    if "text" in delta:
                        text = delta["text"]
                        cache_message.append(text)
                        yield f"{json.dumps({"data":text})}"
                    if "reasoningContent" in delta:
                        reason = delta["reasoningContent"]
                        if "text" in reason:
                            reason_text = reason["text"]
                            reasoning_cache_message.append(reason_text)
                            yield f"{json.dumps({"reasoning_data":reason_text})}"
                        if "signature" in reason:
                            signature = reason["signature"]
                            yield f"{json.dumps({"event":f"signature:{signature}"})}"
                if "messageStart" in event:
                    message_start = event["messageStart"]
                    role = message_start["role"]
                    yield f"{json.dumps({"event":f"start:{role}"})}"
                if "messageStop" in event:
                    message_stop = event["messageStop"]
                    reason = message_stop["stopReason"]
                    yield f"{json.dumps({"event":f"stop:{reason}"})}"
        self.chat_man.add_assistant_response("".join(cache_message))

    def update_system_prompt(self, message):
        self.role.update(message)
        sys_message = self.role_system_template.substitute(self.role)
        self.system_prompt = sys_message

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
