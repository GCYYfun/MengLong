import fastapi_poe as fp
import asyncio
import os
from ..provider import Provider
from .converter import PoeConverter
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
        
        # 如果stream为True，则返回流式响应
        if kwargs.get("stream", False):
            return self.chat_stream(model_id, messages, **kwargs)
        else:
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
        # 使用类级别的事件循环
        if not hasattr(self, '_loop'):
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        
        def stream_wrapper():
            async def get_stream():
                try:
                    poe_messages = self.converter.convert_request(messages)
                    
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
                    else:
                        yield ChatStreamResponse(message=StreamMessage(
                            delta=ContentDelta(text_content=""),
                            finish_reason="stop"
                        ))
                        pass
                except Exception as e:
                    # 在实际生产环境中，应该更妥善地处理异常
                    yield ChatStreamResponse(message=StreamMessage(
                        delta=ContentDelta(text_content=f"错误: {str(e)}"),
                        finish_reason="error"
                    ))
            
            # 使用类级别的事件循环
            async_gen = get_stream()
            try:
                while True:
                    try:
                        future = asyncio.ensure_future(async_gen.__anext__(), loop=self._loop)
                        result = self._loop.run_until_complete(future)
                        yield result
                    except StopAsyncIteration:
                        break
            finally:
                # 确保正确关闭异步生成器
                if hasattr(async_gen, 'aclose'):
                    self._loop.run_until_complete(async_gen.aclose())
                # 确保取消所有未完成的任务
                pending = asyncio.all_tasks(loop=self._loop)
                for task in pending:
                    task.cancel()
                # 让事件循环处理所有任务取消
                if pending:
                    self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                
        # 返回同步生成器
        return stream_wrapper()