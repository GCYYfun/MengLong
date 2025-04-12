#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool Call Demo for OpenAI and DeepSeek models
=============================================

This demo shows how to use tool calls with both OpenAI and DeepSeek models in the MengLong framework.
"""

from typing import List, Dict, Any, Optional
import json
from mlong.model_interface import Model
from mlong.model_interface.utils import user, assistant, system, tool


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
    print(f"Weather tool called for {location} in {unit}")
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


def openai_tool_call_demo():
    """Demo of tool calls using OpenAI models"""
    print("\n=== OpenAI Tool Call Demo ===\n")

    model = Model(model_id="gpt-4o")

    # System message that instructs the model to use tools
    messages = [
        system(
            "You are a helpful assistant that can use tools to answer user questions."
        ),
        user("What's the weather like in Beijing?"),
    ]

    # Call the model with tool definitions
    response = model.chat(
        messages=messages,
        model_id="gpt-4o",  # Using GPT-4o model from OpenAI
        tools=[weather_tool],
        tool_choice="auto",
    )

    print("Response from model:")
    print(response)

    # Check if there are tool calls in the response
    if hasattr(response.message, "tool_calls") and response.message.tool_calls:
        print("Model requested to use a tool:")
        for tool_call in response.message.tool_calls:
            print(f"Tool: {tool_call.function.name}")
            print(f"Arguments: {tool_call.function.arguments}")

            # Parse the arguments and call the appropriate function
            if tool_call.function.name == "get_weather":
                args = json.loads(tool_call.function.arguments)
                weather_result = get_weather(**args)

                # Add the tool response to messages
                messages.append(
                    assistant(
                        tool_calls=[
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": tool_call.function.name,
                                    "arguments": tool_call.function.arguments,
                                },
                            }
                        ],
                    )
                )

                messages.append(
                    tool(
                        tool_call_id=tool_call.id,
                        content=json.dumps(weather_result),
                    )
                )

        # Get the final response from the model
        final_response = model.chat(messages=messages, model_id="gpt-4o")
        print("\nFinal Response:")
        print(final_response.message.content)
        # print("Tool response:", final_response.message.tool_calls[0].content)
    # Check if there are tool calls in the response
    else:
        print("No tool calls were made.")
        print("Response:", response.message.content)


def deepseek_tool_call_demo():
    """Demo of tool calls using DeepSeek models"""
    print("\n=== DeepSeek Tool Call Demo ===\n")

    model = Model(model_id="deepseek-chat")

    # System message that instructs the model to use tools
    messages = [
        system(
            "You are a helpful assistant that can use tools to answer user questions."
        ),
        user("What's the weather like in Shanghai?"),
    ]

    # Call the model with tool definitions
    response = model.chat(
        messages=messages,
        model_id="deepseek-reasoner",  # Using DeepSeek chat model
        tools=[weather_tool],
        tool_choice="auto",
    )

    # Check if there are tool calls in the response
    if hasattr(response.message, "tool_calls") and response.message.tool_calls:
        print("Model requested to use a tool:")
        for tool_call in response.message.tool_calls:
            print(tool_call)
            print(f"Tool: {tool_call.function.name}")
            print(f"Arguments: {tool_call.function.arguments}")

            # Parse the arguments and call the appropriate function
            if tool_call.function.name == "get_weather":
                args = json.loads(tool_call.function.arguments)
                weather_result = get_weather(**args)

                # Add the tool response to messages

                messages.append(
                    assistant(
                        tool_calls=[
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": tool_call.function.name,
                                    "arguments": tool_call.function.arguments,
                                },
                            }
                        ],
                    )
                )

                messages.append(
                    tool(tool_call_id=tool_call.id, content=json.dumps(weather_result))
                )

        print("step2")
        # Get the final response from the model
        final_response = model.chat(messages=messages, model_id="deepseek-chat")
        print("\nFinal Response:")
        print(final_response.message.content)
    else:
        print("No tool calls were made.")
        print("Response:", response.message.content)


def main():
    """Main function to run the demos"""
    print("Starting Tool Call Demo...")

    # try:
    # Run OpenAI tool call demo
    # openai_tool_call_demo()

    # Run DeepSeek tool call demo
    deepseek_tool_call_demo()

    # except Exception as e:
    #     print(f"Error during demo: {e}")

    print("\nTool Call Demo completed.")


if __name__ == "__main__":
    main()
