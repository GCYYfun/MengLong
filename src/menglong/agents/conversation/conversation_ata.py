import json
from string import Template

from ..role_play import RoleAgent
from ..component.context_manager import ATAContextManager


class ATAConversation:
    """Agent to Agent"""

    def __init__(
        self,
        topic: dict = None,
        active_role: dict = None,
        passive_role: dict = None,
        model_id: str = None,
    ):
        self.active = RoleAgent(active_role, model_id=model_id)
        self.passive = RoleAgent(passive_role, model_id=model_id)

        self.topic = Template(topic)
        self.add_topic_to_context()

        self.active_end = False
        self.passive_end = False

        self.end_identify = "END"  # 结束标识

        self.context_manager = ATAContextManager()
        self.context_manager.topic.system = self.active_topic

    def add_topic_to_context(self):  # TODO specific topic
        # 检测 tempalte 是否有变量
        if not isinstance(self.topic, Template):
            raise ValueError("Topic must be a Template object.")
        variables = self.topic.get_identifiers()
        print("模板中的变量:", variables)

        # 准备替换的变量值
        active_data = self.active.role_var.copy()
        passive_data = self.passive.role_var.copy()

        # 检查模板中的变量是否都已提供值
        if all(var in active_data for var in variables):
            # 替换变量
            self.active_topic = self.topic.safe_substitute(active_data)
        if all(var in passive_data for var in variables):
            # 替换变量
            self.passive_topic = self.topic.safe_substitute(passive_data)

        self.passive.update_system_prompt({"topic": f"{self.passive_topic}"})

    def update_topic(self, topic):  # TODO specific topic
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
            if (
                len(self.context_manager.topic.messages) == 0
                or len(self.context_manager.topic.messages) == 1
            ):
                active_res = self.active.chat(self.active_topic)
                # print(f"[system]\n\n{self.active.context_manager.system}")
                print(f"-------------------------")
                print(f"{self.active.role_var['name']}: \n{active_res}")
                print(f"-------------------------")
                # print()
            else:
                active_res = self.active.chat(passive_res)
                # print(f"[system]\n\n{self.active.context_manager.system}")
                print(f"-------------------------")
                print(f"{self.active.role_var['name']}: \n{active_res}")
                print(f"------------------------")
                # print()

            self.context_manager.topic.add_user_message(active_res)
            # 检测回复包含结束标志
            if self.is_over(a_res=active_res):
                break

            passive_res = self.passive.chat(active_res)
            # print(f"[system]\n\n{self.passive.context_manager.system}")
            print(f"-------------------------")
            print(f"{self.passive.role_var['name']}:  \n{passive_res}")
            print(f"-------------------------")
            # print()
            self.context_manager.topic.add_assistant_response(passive_res)

            if self.is_over(p_res=passive_res):
                break
        messages = self.context_manager.topic.messages
        self.context_manager.active = self.active.context_manager
        self.context_manager.passive = self.passive.context_manager
        messages = self.replace_role_name(
            messages, self.active.role_var["name"], self.passive.role_var["name"]
        )

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
            if (
                len(self.context_manager.topic.messages) == 0
                or len(self.context_manager.topic.messages) == 1
            ):
                active_res = self.active.chat_stream(self.active_topic)
                for item in active_res:
                    # i = json.loads(item)
                    if "data" in item:
                        item = item["data"]
                        cache_message.append(item)
                    # print(item)
                    yield item
            else:
                active_res = self.active.chat_stream(passive_res)
                for item in active_res:
                    # i = json.loads(item)
                    if "data" in item:
                        item = item["data"]
                        cache_message.append(item)
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
            passive_res = self.passive.chat_stream(active_res)
            for item in passive_res:
                # i = json.loads(item)
                if "data" in item:
                    item = item["data"]
                    cache_message.append(item)
                # print(item)
                yield item
            passive_res = "".join(cache_message)
            self.context_manager.topic.add_assistant_response(passive_res)
            cache_message.clear()

            if self.is_over(p_res=passive_res):
                # print("Passive End")
                pending = False
                cache_message.clear()

    def replace_role_name(self, messages, user, assistant):
        role_play_messages = messages
        for message in role_play_messages:
            if message.role == "user":
                message.role = user
            elif message.role == "assistant":
                message.role = assistant
            else:
                message.role = "background"
        return role_play_messages

    def set_end_identify(self, identifier: str = "END"):
        """结束标识"""
        self.end_identify = identifier

    def is_over(self, a_res: str = None, p_res: str = None):
        if a_res is not None:
            if not self.active_end and self.end_identify in a_res:
                self.active_end = True
        if p_res is not None:
            if not self.passive_end and self.end_identify in p_res:
                self.passive_end = True
        if self.active_end and self.passive_end:
            self.active_end = False
            self.passive_end = False
            return True
        return False
