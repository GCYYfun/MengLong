import google as genai
from ..provider import Provider
from ..schema.response import ChatResponse, ChatStreamResponse, Choice, MessageContent, EmbedResponse

class GoogleProvider(Provider):
    
    provider_name = "google"

    def __init__(self, config: dict):
        super().__init__(config)
        self.client = genai.GenerativeModel("gemini-1.5-flash")

    """==== MLong Interface Adapter ===="""

    def normalize_chat_response(self, response: dict, thinking_mode: bool) -> ChatResponse:
        return ChatResponse(
            id=response.id,
            object=response.object,
            created=response.created,
            choices=response.choices,
            usage=response.usage
        )
    
    def normalize_stream_response(self, response: dict, thinking_mode: bool) -> ChatStreamResponse:
        return ChatStreamResponse(
            id=response.id,
            object=response.object,
            created=response.created,
            choices=response.choices,
            usage=response.usage
        )

    """==== 模型方法 ===="""

    def chat(self, messages: list, **kwargs) -> ChatResponse:
        return self.client.chat(messages)
    
    def embed(self, model_id: str, texts: [], **kwargs) -> EmbedResponse:
        return self.client.embed(texts)
    
    
    