import openai
import os
from ..provider import Provider
from ..schema.ml_response import ChatStreamResponse, StreamMessage, ContentDelta
from .converter import DeepseekConverter


class DeepseekProvider(Provider):
    def __init__(self, config):
        """
        Initialize the DeepSeek provider with the given configuration.
        Pass the entire configuration dictionary to the OpenAI client constructor.
        """
        # Ensure API key is provided either in config or via environment variable
        config.setdefault("api_key", os.getenv("DEEPSEEK_API_KEY"))
        if not config["api_key"]:
            raise ValueError(
                "DeepSeek API key is missing. Please provide it in the config or set the OPENAI_API_KEY environment variable."
            )
        config["base_url"] = "https://api.deepseek.com"

        # NOTE: We could choose to remove above lines for api_key since OpenAI will automatically
        # infer certain values from the environment variables.
        # Eg: OPENAI_API_KEY, OPENAI_ORG_ID, OPENAI_PROJECT_ID. Except for OPEN_AI_BASE_URL which has to be the deepseek url

        # Pass the entire config to the OpenAI client constructor
        self.client = openai.OpenAI(**config)
        self.converter = DeepseekConverter()

    def is_reasoning(self, model_id):
        if model_id == "deepseek-reasoner":
            return True
        else:
            return False

    def chat(self, model_id, messages, **kwargs):
        # Any exception raised by OpenAI will be returned to the caller.
        # Maybe we should catch them and raise a custom LLMError.
        DeepseekConverter.reasoning = self.is_reasoning(model_id)

        messages = self.converter.convert_request(messages)

        if kwargs.get("tools"):
            kwargs["tools"] = self.converter.convert_tools(kwargs["tools"], model_id)
        # 如果stream为True，则返回流式响应
        if kwargs.get("stream", False):
            return self.chat_stream(model_id, messages, **kwargs)
        else:
            response = self.client.chat.completions.create(
                model=model_id,
                messages=messages,
                **kwargs,  # Pass any additional arguments to the OpenAI API
            )
            response = self.converter.normalize_response(response)
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
