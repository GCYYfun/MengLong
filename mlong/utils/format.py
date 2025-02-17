user = lambda text: {
    "role": "user",
    "content": text,
}
assistant = lambda text: {
    "role": "assistant",
    "content": text,
}
system = lambda text: {
    "role": "system",
    "content": text,
}

stream_to_str = lambda stream: "".join(
    [
        event["contentBlockDelta"]["delta"]["text"]
        for event in stream
        if "contentBlockDelta" in event
    ]
)


def format_messages_for_aws(messages):
    system_messages = []
    prompt_messages = []
    for message in messages:
        if message["role"] == "system":
            system_messages.append({"text": message["content"]})
        else:
            prompt_messages.append(
                {"role": message["role"], "content": [{"text": message["content"]}]}
            )
    return system_messages, prompt_messages
