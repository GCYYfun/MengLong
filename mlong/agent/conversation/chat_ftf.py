import json
from string import Template

from mlong.agent.role import FluctLight
from mlong.component.context_manager import ATAContextManager


class FLToFLChat:
    """Agent to Agent"""

    def __init__(
        self,
        topic=None,
        active_role: dict = None,
        passive_role: dict = None,
        memory_space: str = None,
        model_id: str = None,
    ):
        self.active = FluctLight(active_role, memory_space,model_id=model_id)
        self.passive = FluctLight(passive_role,memory_space,model_id=model_id)

        self.topic = Template(topic)
        self.add_topic_to_context()

        self.active_end = False
        self.passive_end = False

        self.context_manager = ATAContextManager()
        self.context_manager.topic.system = self.active_topic

    def add_topic_to_context(self): # TODO specific topic
        self.active_topic = self.topic.substitute(
            name=self.active.role_info["name"],
            peer_name=self.passive.role_info["name"],
            peer_info=self.passive.role_info,
        )
        self.passive_topic = self.topic.substitute(
            name=self.passive.role_info["name"],
            peer_name=self.active.role_info["name"],
            peer_info=self.active.role_info,
        )

        self.passive.update_system_prompt({"topic":f"{self.passive_topic}"})

    def update_topic(self, topic): # TODO specific topic
        pass

    def chat(self, topic=None):
        if topic is None:
            topic = self.topic
        index = 0
        # 当对话五次后结束
        active_res = ""
        passive_res = ""
        while True:  # TODO Interrupted
            index += 1
            # print(f"对话次数: {index}")
            if len(self.context_manager.topic.messages) == 0 or len(self.context_manager.topic.messages) == 1:
                active_res = self.active.chat_with_mem(self.active_topic)
                # print(f"[system]\n\n{self.active.context_manager.system}")
                print(f"{self.active.role_info["name"]}: \n{active_res}")
                # print()
            else:
                active_res = self.active.chat_with_mem(passive_res)
                # print(f"[system]\n\n{self.active.context_manager.system}")
                print(f"{self.active.role_info["name"]}: \n{active_res}")
                # print()

            self.context_manager.topic.add_user_message(active_res)
            # 检测回复包含结束标志
            if self.is_over(a_res=active_res):
                break

            passive_res = self.passive.chat_with_mem(active_res)
            # print(f"[system]\n\n{self.passive.context_manager.system}")
            print(f"{self.passive.role_info["name"]}:  \n{passive_res}")
            # print()
            self.context_manager.topic.add_assistant_response(passive_res)

            if self.is_over(p_res=passive_res):
                break
        messages = self.context_manager.topic.messages
        self.context_manager.active = self.active.context_manager
        self.context_manager.passive = self.passive.context_manager
        messages = self.replace_role_name(messages, self.active.role_info["name"], self.passive.role_info["name"])
        # mem
        self.active.summary()
        self.passive.summary()
        return messages

    def chat_stream(self, topic=None):
        pending = True
        cache_message = []
        if topic is None:
            topic = self.topic
        index = 0
        # 当对话五次后结束
        active_res = ""
        passive_res = ""
        while pending:  # TODO Interrupted
            index += 1
            # print(f"对话次数: {index}")
            # print("ACTIVE:")
            if len(self.context_manager.topic.messages) == 0 or len(self.context_manager.topic.messages) == 1:
                active_res = self.active.chat_stream_with_mem(self.active_topic)
                for item in active_res:
                    i = json.loads(item)
                    if "data" in i:
                        i = i["data"]
                        cache_message.append(i)
                    # print(item)
                    yield item
            else:
                active_res = self.active.chat_stream_with_mem(passive_res)
                for item in active_res:
                    i = json.loads(item)
                    if "data" in i:
                        i = i["data"]
                        cache_message.append(i)
                    # print(item)
                    yield item
            active_res = "".join(cache_message)
            self.context_manager.topic.add_user_message(active_res)
            # 检测回复包含结束标志
            if self.is_over(a_res=active_res):
                # print("Active End")
                pending = False
                cache_message.clear()
                break
            # reset
            cache_message.clear()
            # print("PASSIVE:")
            passive_res = self.passive.chat_stream_with_mem(active_res)
            for item in passive_res:
                i = json.loads(item)
                if "data" in i:
                    i = i["data"]
                    cache_message.append(i)
                # print(item)
                yield item
            passive_res = "".join(cache_message)
            self.context_manager.topic.add_assistant_response(passive_res)

            if self.is_over(p_res=passive_res):
                # print("Passive End")
                pending = False
        self.active.summary()
        self.passive.summary()
    def replace_role_name(self, messages, user, assistant):
        role_play_messages = messages
        for message in role_play_messages:
            if message["role"] == "user":
                message["role"] = user
            elif message["role"] == "assistant":
                message["role"] = assistant
            else:
                message["role"] = "background"
        return role_play_messages

    def is_over(self, a_res: str = None, p_res: str = None):
        if a_res is not None:
            if not self.active_end and "[END]" in a_res:
                self.active_end = True
        if p_res is not None:
            if not self.passive_end and "[END]" in p_res:
                self.passive_end = True
        if self.active_end and self.passive_end:
            self.active_end = False
            self.passive_end = False
            return True
        return False
