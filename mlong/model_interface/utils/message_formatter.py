from typing import Dict, List, Any, override


def user(text: str) -> Dict[str, str]:
    """
    创建用户角色的消息格式

    Args:
        text: 用户消息内容

    Returns:
        格式化的用户消息字典
    """
    return {
        "role": "user",
        "content": text,
    }


def assistant(text: str) -> Dict[str, str]:
    """
    创建助手角色的消息格式

    Args:
        text: 助手消息内容

    Returns:
        格式化的助手消息字典
    """
    return {
        "role": "assistant",
        "content": text,
    }


def system(text: str) -> Dict[str, str]:
    """
    创建系统角色的消息格式

    Args:
        text: 系统消息内容

    Returns:
        格式化的系统消息字典
    """
    return {
        "role": "system",
        "content": text,
    }


def tool(tool_call_id: str, content: str) -> Dict[str, str]:
    """
    创建工具角色的消息格式

    Args:
        tool_call_id: 工具调用 ID
        content: 工具消息内容

    Returns:
        格式化的工具消息字典
    """
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": content,
    }


def aws_stream_to_str(stream: List[Dict[str, Any]]) -> str:
    """
    将流式响应转换为字符串

    Args:
        stream: 流式响应事件列表

    Returns:
        合并后的文本内容
    """
    result = []
    for event in stream:
        try:
            if "contentBlockDelta" in event:
                result.append(event["contentBlockDelta"]["delta"]["text"])
        except (KeyError, TypeError):
            continue
    return "".join(result)


def format_messages_for_aws(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    将消息格式转换为 aws converse api 要求的格式

    Args:
        messages: 消息列表，每个消息为一个字典，包含角色和内容

    Returns:
        转换后的消息列表
    """
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
