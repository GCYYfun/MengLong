import openai
import os
from ..provider import Provider
from ..utils.converter import OpenAIConverter
from ..schema.response import ChatResponse, ChatStreamResponse, Choice, MessageContent, EmbedResponse

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
        try:
            # format_messages = self.converter.convert_request(messages)
            response = self.client.chat.completions.create(
                model=model_id,
                messages=messages,
                **kwargs,  # Pass any additional arguments to the OpenAI API
            )
            return response
        except Exception as e:
            raise f"An error occurred: {e}"