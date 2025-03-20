import fastapi_poe as fp
import asyncio
import os
from ..provider import Provider
from ..utils.converter import PoeConverter
from ..schema.response import StreamMessage, ContentDelta, ChatStreamResponse



class PoeProvider(Provider):
    def __init__(self, config):
        super().__init__(config)
        config.setdefault("api_key", os.getenv("POE_API_KEY"))
        if not config["api_key"]:
            raise ValueError(
                "Poe API key is missing. Please provide it in the config or set the POE_API_KEY environment variable."
            )
        self.key = config["api_key"]
        self.converter = PoeConverter()

    def chat(self, model_id, messages, **kwargs):
        async def one_step(text):
            messages = self.converter.convert_request(text)
            try:
                response = ""
                async for partial in fp.get_bot_response(
                    messages=messages,
                    bot_name=model_id,
                    api_key=self.key,
                ):
                    response += partial.text
                return self.converter.normalize_response(response)
            except Exception as e:
                return str(e)
        response = asyncio.run(one_step(messages))
        return response
        
    def chat_stream(self, model_id, messages, **kwargs):
        """
        Generate a streaming chat response.
        
        Args:
            model_id: The Poe bot name
            messages: List of messages in the conversation
            **kwargs: Additional arguments (not used for Poe)
            
        Returns:
            A generator yielding stream responses
        """
        # 将异步生成器转换为同步生成器的辅助函数
        def stream_wrapper():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def get_stream():
                try:
                    poe_messages = self.converter.convert_request(messages)
                    index = 0
                    
                    async for partial in fp.get_bot_response(
                        messages=poe_messages,
                        bot_name=model_id,
                        api_key=self.key,
                    ):
                        # 创建流式响应
                        delta = ContentDelta(
                            text_content=partial.text,
                            reasoning_content=None  # Poe不提供reasoning_content
                        )
                        message = StreamMessage(
                            delta=delta,
                            finish_reason=None  # 只有在流结束时才会有finish_reason
                        )
                        yield ChatStreamResponse(message=message)
                except Exception as e:
                    # 在实际生产环境中，应该更妥善地处理异常
                    yield ChatStreamResponse(message=StreamMessage(
                        delta=ContentDelta(text_content=f"错误: {str(e)}"),
                        finish_reason="error"
                    ))
            
            # 使用loop.run_until_complete运行异步生成器，并逐个返回结果
            async_gen = get_stream()
            try:
                while True:
                    try:
                        result = loop.run_until_complete(async_gen.__anext__())
                        yield result
                    except StopAsyncIteration:
                        break
            finally:
                loop.close()
                
        # 返回同步生成器
        return stream_wrapper()