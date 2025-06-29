import openai
import os
from ..provider import Provider
from ..schema.ml_response import ChatStreamResponse, StreamMessage, ContentDelta
from .converter import InfinigenceConverter

import requests

# url = "https://cloud.infini-ai.com/maas/v1/chat/completions"

# payload = {"model": "deepseek-r1", "messages": [{"role": "user", "content": "你是谁"}]}
# headers = {"Content-Type": "application/json", "Authorization": "Bearer $API_KEY"}

# response = requests.post(url, json=payload, headers=headers)

# print(response.json())


class InfinigenceProvider(Provider):
    def __init__(self, config):
        """
        Initialize the Infinigence provider with the given configuration.
        Pass the entire configuration dictionary to the OpenAI client constructor.
        """
        # Ensure API key is provided either in config or via environment variable
        config.setdefault("api_key", os.getenv("INFINIGENCE_API_KEY"))
        if not config["api_key"]:
            raise ValueError(
                "Infinigence API key is missing. Please provide it in the config or set the OPENAI_API_KEY environment variable."
            )
        config["base_url"] = "https://cloud.infini-ai.com/maas"
        self.base_url = config.get("base_url")
        self.api_key = config.get("api_key")
        # NOTE: We could choose to remove above lines for api_key since OpenAI will automatically
        # infer certain values from the environment variables.
        # Eg: OPENAI_API_KEY, OPENAI_ORG_ID, OPENAI_PROJECT_ID. Except for OPEN_AI_BASE_URL which has to be the deepseek url

        # Pass the entire config to the OpenAI client constructor
        # self.client = openai.OpenAI(**config)
        self.converter = InfinigenceConverter()

    def is_reasoning(self, model_id):
        if model_id == "infinigence-reasoner":
            return True
        else:
            return False

    def chat(self, model_id, messages, **kwargs):
        # Any exception raised by OpenAI will be returned to the caller.
        # Maybe we should catch them and raise a custom LLMError.
        InfinigenceConverter.reasoning = self.is_reasoning(model_id)
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        messages = self.converter.convert_request(messages)
        payload = {"model": model_id, "messages": messages}
        if kwargs.get("tools", None):
            format_tools = self.converter.convert_tools(kwargs["tools"])
            payload["tools"] = format_tools

        debug = kwargs.get("debug", False)

        # 如果stream为True，则返回流式响应
        if kwargs.get("stream", False):
            return self.chat_stream(model_id, messages, **kwargs)
        else:
            response = requests.post(url, json=payload, headers=headers)
            response = self.converter.normalize_response(response.json(), debug=debug)
            return response

    def chat_stream(self, model_id, messages, **kwargs):
        """
        Generate a streaming chat response.

        Args:
            model_id: The DeepSeek model identifier
            messages: List of messages in the conversation
            **kwargs: Additional arguments to pass to the API

        Returns:
            A generator yielding stream responses
        """
        # 设置流式响应参数,无意义但确保
        kwargs["stream"] = True

        # 创建流式响应
        response_stream = self.client.chat.completions.create(
            model=model_id, messages=messages, **kwargs
        )
        return self.converter.normalize_stream_response(response_stream)
