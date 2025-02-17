import json
from string import Template

from mlong.agent.role_play.role_play_agent import RolePlayAgent
from mlong.types.type_chat import ChatManager


class TwoRolePlayAgent:
    def __init__(
        self,
        topic=None,
        active_role: RolePlayAgent = None,
        passive_role: RolePlayAgent = None,
    ):
        self.active = active_role
        self.passive = passive_role

        self.topic = Template(topic)
        self.process_topic()

        self.active_end = False
        self.passive_end = False

        self.chat_man = ChatManager()
        self.chat_man.system_message(self.active_topic)

    def process_topic(self):
        self.active_topic = self.topic.substitute(
            name=self.active.name,
            peer_name=self.passive.name,
            peer_info=self.passive.role_system,
        )
        self.passive_topic = self.topic.substitute(
            name=self.passive.name,
            peer_name=self.active.name,
            peer_info=self.active.role_system,
        )
        passive_system = self.passive.chat_man.system

        self.passive.chat_man.system_message(
            passive_system + f"\n\n{self.passive_topic}"
        )

    def chat(self, topic=None):
        if topic is None:
            topic = self.topic
        index = 0
        # 当对话五次后结束
        while True:  # TODO Interrupted
            index += 1
            print(f"对话次数: {index}")
            if len(self.chat_man.messages) == 0 or len(self.chat_man.messages) == 1:
                active_res = self.active.chat(self.active_topic)
                print(f"{self.active.name}: \n{active_res}")
                print()
            else:
                active_res = self.active.chat(passive_res)
                print(f"{self.active.name}: \n{self.active.chat_man.messages}")
                # print(f"{self.active.name}: \n{active_res}")
                print()

            self.chat_man.add_user_message(active_res)
            # 检测回复包含结束标志
            if self.is_over(a_res=active_res):
                break

            passive_res = self.passive.chat(active_res)
            print(f"{self.passive.name}:  \n{self.passive.chat_man.messages}")
            # print(f"{self.passive.name}:  \n{passive_res}")
            print()
            self.chat_man.add_assistant_response(passive_res)

            if self.is_over(p_res=passive_res):
                break
        messages = self.chat_man.messages
        messages = self.replace_role_name(messages, self.active.name, self.passive.name)

        return messages

    def chat_stream(self, topic=None):
        pending = True
        cache_message = []
        if topic is None:
            topic = self.topic
        index = 0
        # 当对话五次后结束
        while pending:  # TODO Interrupted
            index += 1
            print(f"对话次数: {index}")
            if len(self.chat_man.messages) == 0 or len(self.chat_man.messages) == 1:
                active_res = self.active.chat_stream(self.active_topic)
                for item in active_res:
                    i = json.loads(item)
                    if "data" in i:
                        i = i["data"]
                        cache_message.append(i)
                    yield item
            else:
                active_res = self.active.chat_stream(passive_res)
                for item in active_res:
                    i = json.loads(item)
                    if "data" in i:
                        i = i["data"]
                        cache_message.append(i)
                    yield item
            active_res = "".join(cache_message)
            self.chat_man.add_user_message(active_res)
            # 检测回复包含结束标志
            if self.is_over(a_res=active_res):
                pending = False
                cache_message.clear()
                break
            # reset
            cache_message.clear()
            passive_res = self.passive.chat_stream(active_res)
            for item in passive_res:
                i = json.loads(item)
                if "data" in i:
                    i = i["data"]
                    cache_message.append(i)
                yield item
            passive_res = "".join(cache_message)
            self.chat_man.add_assistant_response(passive_res)

            if self.is_over(p_res=passive_res):
                pending = False
        # messages = self.chat_man.messages
        # messages = self.replace_role_name(messages, self.active.name, self.passive.name)

        # return messages

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
            if self.active_end == False and "[END]" in a_res:
                self.active_end = True
        if p_res is not None:
            if self.passive_end == False and "[END]" in p_res:
                self.passive_end = True
        if self.active_end and self.passive_end:
            self.active_end = False
            self.passive_end = False
            return True
        return False
