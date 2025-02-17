def get_provider_and_model(model_id):
    provider = model_id.__class__.__name__.lower()
    model = model_id.value
    return provider, model


async def parse_model_stream_response(response, cache_message=None):
    s = response.stream
    if s:
        for event in s:
            # 将事件转换为字典
            # event = await event.json()
            if "contentBlockDelta" in event:
                delta = event["contentBlockDelta"]
                if "delta" in delta and "text" in delta["delta"]:
                    t = delta["delta"]["text"]
                    if cache_message is not None:
                        cache_message.append(t)
                    yield f"{t}"


async def parse_text_stream_response(text_stream, cache_message=None):
    async for text in text_stream:
        if text:
            t = text
            if cache_message is not None:
                cache_message.append(t)
            yield f"{t}"
