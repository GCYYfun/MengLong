from mlong.utils import user, assistant, system


class ChatResponse:
    def __init__(self):
        self.choices = [Choice()]

    # def text():
    #     return self.choices[0].message.content


class ChatStreamResponse:
    def __init__(self):
        self.id = None
        self.stream = None


class Choice:
    def __init__(self):
        self.message = Message()


class Message:
    def __init__(self):
        self.reasoning_content = None
        self.content = None


class ChatManager:

    def __init__(self):
        self.context = []

    def reset(self):
        self.context = []

    def clear(self):
        if len(self.context) != 0 and self.context[0]["role"] == "system":
            self.context = self.context[:1]

    @property
    def system(self):
        if len(self.context) != 0:
            if self.context[0]["role"] == "system":
                return self.context[0]["content"]
        return None

    @property
    def messages(self):
        return self.context

    @system.setter
    def system(self, message):
        if len(self.context) != 0:
            if self.context[0]["role"] == "system":
                self.context[0]["content"] = message
        else:
            self.context.append(system(message))

    def add_user_message(self, message):
        # 检查是否有连续的用户消息
        if len(self.context) == 0:
            self.context.append(user(message))
        elif (
            self.context[-1]["role"] == "assistant"
            or self.context[-1]["role"] == "system"
        ):
            self.context.append(user(message))
        else:
            raise ValueError(
                f"User message must follow system or assistant message,now you context is {self.context},message is {message}"
            )

    def add_assistant_response(self, message: str):
        if self.context and self.context[-1]["role"] == "user":
            # message = message.choices[0].message.content
            self.context.append(assistant(message))
        else:
            raise ValueError("Assistant response must follow user message")

    def pop(self):
        return self.context.pop()
