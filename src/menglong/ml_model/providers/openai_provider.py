import openai
import os
from ..provider import Provider
from .converter import OpenAIConverter
from ..schema.ml_response import (
    ChatResponse,
    ChatStreamResponse,
    Message,
    Content,
    EmbedResponse,
    StreamMessage,
    ContentDelta,
)


class OpenaiProvider(Provider):
    provider_name = "openai"

    def __init__(self, config):
        """
        Initialize the OpenAI provider with the given configuration.
        Pass the entire configuration dictionary to the OpenAI client constructor.
        """
        # Ensure API key is provided either in config or via environment variable
        config.setdefault("api_key", os.getenv("OPENAI_API_KEY"))
        if not config["api_key"]:
            raise ValueError(
                "OpenAI API key is missing. Please provide it in the config or set the OPENAI_API_KEY environment variable."
            )

        # NOTE: We could choose to remove above lines for api_key since OpenAI will automatically
        # infer certain values from the environment variables.
        # Eg: OPENAI_API_KEY, OPENAI_ORG_ID, OPENAI_PROJECT_ID, OPENAI_BASE_URL, etc.

        # Pass the entire config to the OpenAI client constructor
        self.client = openai.OpenAI(**config)
        self.converter = OpenAIConverter()

    def chat(self, model_id, messages, **kwargs):
        # Any exception raised by OpenAI will be returned to the caller.
        # Maybe we should catch them and raise a custom LLMError.
        messages = self.converter.convert_request(messages)
        try:
            # format_messages = self.converter.convert_request(messages)
            response = self.client.chat.completions.create(
                model=model_id,
                messages=messages,
                **kwargs,  # Pass any additional arguments to the OpenAI API
            )
            return self.converter.normalize_response(response)
        except Exception as e:
            raise f"An error occurred: {e}"

    def chat_stream(self, model_id, messages, **kwargs):
        """
        Generate a streaming chat response.

        Args:
            model_id: The OpenAI model identifier
            messages: List of messages in the conversation
            **kwargs: Additional arguments to pass to the API

        Returns:
            A generator yielding stream responses
        """
        # 设置流式响应参数
        kwargs["stream"] = True

        # 创建流式响应
        response_stream = self.client.chat.completions.create(
            model=model_id, messages=messages, **kwargs
        )

        return self.converter.normalize_stream_response(response_stream)

        # 返回生成器
        # for chunk in response_stream:
        #     if chunk.choices:
        #         choice = chunk.choices[0]
        #         # 如果delta中有content字段
        #         content = choice.delta.content if hasattr(choice.delta, 'content') and choice.delta.content else None

        #         # 检查是否有推理内容（对于某些模型，如GPT-4 Turbo可能有）
        #         reasoning_content = None
        #         if hasattr(choice.delta, 'tool_calls') and choice.delta.tool_calls:
        #             # 这里假设reasoning_content可能存储在tool_calls中
        #             # 具体实现可能需要根据实际情况调整
        #             pass

        #         delta = ContentDelta(
        #             text_content=content,
        #             reasoning_content=reasoning_content
        #         )

        #         stream_choice = StreamMessage(
        #             delta=delta,
        #             finish_reason=choice.finish_reason
        #         )

        #         yield ChatStreamResponse(message=stream_choice)
