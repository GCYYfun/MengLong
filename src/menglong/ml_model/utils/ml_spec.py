from typing import Dict, List, Any, override


# def user(text: str) -> Dict[str, str]:
#     """
#     创建用户角色的消息格式

#     Args:
#         text: 用户消息内容

#     Returns:
#         格式化的用户消息字典
#     """
#     return {
#         "role": "user",
#         "content": text,
#     }


# def assistant(text: str) -> Dict[str, str]:
#     """
#     创建助手角色的消息格式

#     Args:
#         text: 助手消息内容

#     Returns:
#         格式化的助手消息字典
#     """
#     return {
#         "role": "assistant",
#         "content": text,
#     }


# def system(text: str) -> Dict[str, str]:
#     """
#     创建系统角色的消息格式

#     Args:
#         text: 系统消息内容

#     Returns:
#         格式化的系统消息字典
#     """
#     return {
#         "role": "system",
#         "content": text,
#     }


# def tool(tool_id: str, content: str, mode: str) -> Dict[str, str]:
#     """
#     创建工具角色的消息格式

#     Args:
#         tool_call_id: 工具调用 ID
#         content: 工具消息内容

#     Returns:
#         格式化的工具消息字典
#     """
#     fm = {}
#     if mode == "oai":
#         fm = {
#             "role": "tool",
#             "tool_call_id": tool_id,
#             "content": content,
#         }
#     elif mode == "anthropic":
#         fm = {
#             "role": "user",
#             "content": [
#                 {
#                     "toolResult": {
#                         "toolUseId": tool_id,
#                         "content": [{"json": content}],
#                     }
#                 }
#             ],
#         }
#     else:
#         raise ValueError("Unsupported mode")
#     return fm


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


# def tool_res(msg, mode) -> Dict[str, str]:
#     """
#     创建工具响应格式

#     Args:
#         tool_call_id: 工具调用 ID
#         content: 工具消息内容
#         function_name: 函数名称（可选）
#         function_arguments: 函数参数（可选）

#     Returns:
#         格式化的工具响应字典
#     """
#     fm = {}
#     if mode == "oai":
#         fm = {
#             "role": "assistant",
#             "content": msg.content.text,
#             "tool_calls": [
#                 {
#                     "id": desc.id,
#                     "type": desc.type,
#                     "function": {
#                         "name": desc.name,
#                         "arguments": desc.arguments,
#                     },
#                 }
#                 for desc in msg.tool_desc
#             ],
#         }
#     elif mode == "anthropic":
#         fm = {
#             "role": "assistant",
#             "content": [
#                 msg.content.text,
#                 {
#                     "type": msg.tool_desc[0].type,
#                     "id": msg.tool_desc[0].id,
#                     "name": msg.tool_desc[0].name,
#                     "input": msg.tool_desc[0].arguments,
#                 },
#             ],
#         }
#     else:
#         raise ValueError("Unsupported mode")

#     return fm


oai_tool_format = {
    "name": "tool",
    "description": "A tool that can be used to perform actions.",
    "parameters": {
        "type": "object",
        "properties": {
            "tool_call_id": {
                "type": "string",
                "description": "The ID of the tool call.",
            },
            "content": {
                "type": "string",
                "description": "The content of the tool call.",
            },
        },
        "required": ["tool_call_id", "content"],
    },
}

anthropic_tool_format = {
    "name": "tool",
    "description": "A tool that can be used to perform actions.",
    "parameters": {
        "type": "object",
        "properties": {
            "tool_call_id": {
                "type": "string",
                "description": "The ID of the tool call.",
            },
            "content": {
                "type": "string",
                "description": "The content of the tool call.",
            },
        },
        "required": ["tool_call_id", "content"],
    },
}
