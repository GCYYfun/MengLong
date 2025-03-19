import fastapi_poe as fp
import asyncio
import os
from ..provider import Provider
from ..utils.converter import PoeConverter



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