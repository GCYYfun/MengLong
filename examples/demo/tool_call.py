"""
Tool Call Demo for Models
=============================================

This demo shows how to use tool calls with both OpenAI and DeepSeek models in the MengLong framework.
"""

from typing import List, Dict, Any, Optional
import json
from menglong.ml_model import Model
from menglong.utils.log.logging_tool import (
    print,
    print_rule,
    print_json,
    print_table,
    MessageType,
    configure_logger,
    get_logger,
)

# from menglong.ml_model.utils import user, assistant, system, tool, tool_res
from menglong.ml_model.schema.ml_request import (
    SystemMessage as system,
    ToolMessage as tool,
    AssistantMessage as assistant,
    UserMessage as user,
)


# Define a simple weather tool
def get_weather(location: str, unit: str = "celsius") -> Dict[str, Any]:
    """Get the current weather in a given location.

    Args:
        location: The city and state, e.g. San Francisco, CA
        unit: The unit of temperature, either "celsius" or "fahrenheit"

    Returns:
        Dict containing weather information
    """
    # Simulate weather data (in a real application, you would call a weather API)
    weather_data = {
        "location": location,
        "temperature": 22 if unit == "celsius" else 72,
        "unit": unit,
        "forecast": ["sunny", "windy"],
        "humidity": 60,
    }
    print(f"Weather tool called for {location} in {unit}", MessageType.INFO)
    return weather_data


# Define available tools
weather_tool = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The unit of temperature to use. Infer this from the user's location.",
                },
            },
            "required": ["location"],
        },
    },
}

weather_tool_an = {
    "name": "get_weather",
    "description": "Get the current weather in a given location",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city and state, e.g. San Francisco, CA",
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": 'The unit of temperature, either "celsius" or "fahrenheit"',
            },
        },
        "required": ["location"],
    },
}

weather_tool_aws = {
    "toolSpec": {
        "name": "get_weather",
        "description": "Get the current weather in a given location",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": 'The unit of temperature, either "celsius" or "fahrenheit"',
                    },
                },
                "required": ["location"],
            }
        },
    }
}


def openai_tool_call_demo():

    model = Model(model_id="gpt-4o")

    # System message that instructs the model to use tools
    messages = [
        system(
            content="You are a helpful assistant that can use tools to answer user questions."
        ),
        user(content="What's the weather like in Beijing?"),
    ]

    # Call the model with tool definitions
    response = model.chat(
        messages=messages,
        model_id="gpt-4o",  # Using GPT-4o model from OpenAI
        tools=[weather_tool],
        tool_choice="auto",
    )

    print_rule("Response from model", style="green")
    print_json(response)

    # Check if there are tool calls in the response
    if hasattr(response.message, "tool_desc") and response.message.tool_desc:
        print("Model requested to use a tool:", MessageType.SUCCESS, title="Tool Call")
        for tool_call in response.message.tool_desc:
            print_table(
                [["Name", tool_call.name], ["Arguments", tool_call.arguments]],
                ["Property", "Value"],
                title="Tool Details",
            )

            # Parse the arguments and call the appropriate function
            if tool_call.name == "get_weather":
                args = json.loads(tool_call.arguments)
                weather_result = get_weather(**args)

                # Add the tool response to messages
                print(response.message)
                messages.append(response.message)

                messages.append(
                    tool(
                        tool_id=tool_call.id,
                        content=json.dumps(weather_result),
                    )
                )

        # Get the final response from the model
        final_response = model.chat(messages=messages, model_id="gpt-4o")
        print_rule("Final Response", style="cyan")
        print(final_response.message.content, MessageType.AGENT, use_panel=True)
        # print("Tool response:", final_response.message.tool_calls[0].content)
    # Check if there are tool calls in the response
    else:
        print("No tool calls were made.", MessageType.WARNING)
        print(response.message.content.text, MessageType.AGENT, use_panel=True)


def deepseek_tool_call_demo():
    """Demo of tool calls using DeepSeek models"""
    print_rule("DeepSeek Tool Call Demo", style="blue")

    model = Model(model_id="deepseek-chat")

    # System message that instructs the model to use tools
    messages = [
        system(
            content="You are a helpful assistant that can use tools to answer user questions."
        ),
        user(content="What's the weather like in Shanghai?"),
    ]

    # Call the model with tool definitions
    response = model.chat(
        messages=messages,
        tools=[weather_tool],
        tool_choice="auto",
    )

    # Check if there are tool calls in the response
    if hasattr(response.message, "tool_desc") and response.message.tool_desc:
        print("Model requested to use a tool:", MessageType.SUCCESS, title="Tool Call")
        for tool_call in response.message.tool_desc:
            print_json(tool_call, title="Tool Call Object")
            print_table(
                [["Name", tool_call.name], ["Arguments", tool_call.arguments]],
                ["Property", "Value"],
                title="Tool Details",
            )

            # Parse the arguments and call the appropriate function
            if tool_call.name == "get_weather":
                args = json.loads(tool_call.arguments)
                weather_result = get_weather(**args)

                # Add the tool response to messages

                messages.append(response.message)

                messages.append(
                    tool(tool_id=tool_call.id, content=json.dumps(weather_result))
                )

        print("Processing tool response...", MessageType.INFO)
        # Get the final response from the model
        final_response = model.chat(messages=messages, model_id="deepseek-chat")
        print_rule("Final Response", style="cyan")
        print(final_response.message.content, MessageType.AGENT, use_panel=True)
    else:
        print("No tool calls were made.", MessageType.WARNING)
        print(response.message.content, MessageType.AGENT, use_panel=True)


def anthropic_tool_call_demo():
    """Demo of tool calls using Anthropic models"""
    print("\n=== Anthropic Tool Call Demo ===\n")

    model = Model(model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0")

    # System message that instructs the model to use tools
    messages = [
        system(
            content="You are a helpful assistant that can use tools to answer user questions."
        ),
        user(content="What's the weather like in New York?"),
    ]

    # Call the model with tool definitions
    response = model.chat(
        messages=messages,
        temperature=0.5,
        maxTokens=1000,
        tools=[weather_tool_aws],
        tool_choice={"type": "any"},
    )

    print("Response from model:")
    print(response)

    # Check if there are tool calls in the response
    if hasattr(response.message, "tool_desc") and response.message.tool_desc:
        print("Model requested to use a tool:")
        for tool_desc in response.message.tool_desc:
            print(f"Tool: {tool_desc.name}")
            print(f"Arguments: {tool_desc.arguments}")

            # Parse the arguments and call the appropriate function
            if tool_desc.name == "get_weather":
                args = tool_desc.arguments
                weather_result = get_weather(**args)

                # Add the tool response to messages
                messages.append(response.message)

                messages.append(
                    user(
                        tool_id=tool_desc.id,
                        content=weather_result,
                    )
                )

        print("step2")
        print("messages", messages)
        # Get the final response from the model
        final_response = model.chat(messages=messages, tools=[weather_tool_aws])
        print("Final Response:")
        print(final_response.message.content)
    else:
        print("No tool calls were made.")
        print("Response:", response.message.content)


def main():
    # 配置日志
    configure_logger(log_file="tool_call_demo.log")
    logger = get_logger()

    logger.info("启动工具调用演示")
    print("Starting Tool Call Demo...", MessageType.INFO)

    print_rule("OpenAI Demo", style="green")
    logger.info("开始 OpenAI 工具调用演示")
    openai_tool_call_demo()

    print_rule("DeepSeek Demo", style="blue")
    logger.info("开始 DeepSeek 工具调用演示")
    deepseek_tool_call_demo()

    print_rule("Anthropic Demo", style="magenta")
    logger.info("开始 Anthropic 工具调用演示")
    anthropic_tool_call_demo()

    logger.info("工具调用演示完成")
    print("Tool Call Demo completed.", MessageType.SUCCESS, title="Completed")


if __name__ == "__main__":
    main()
