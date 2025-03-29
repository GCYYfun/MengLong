from typing import Optional
from mlong.agent.base_agent.base_agent import ToolAgent
from mlong.agent.base_agent.tools import tool

from mlong.agent.base_agent.model import MLongModel

# For anthropic: change model_id below to 'anthropic/claude-3-5-sonnet-latest'
model = MLongModel()


@tool
def get_weather(location: str, celsius: Optional[bool] = False) -> str:
    """
    Get weather in the next days at given location.
    Secretly this tool does not care about the location, it hates the weather everywhere.

    Args:
        location: the location
        celsius: the temperature
    """
    return "The weather is UNGODLY with torrential rains and temperatures below -10°C"


agent = ToolAgent(tools=[get_weather], model=model, verbosity_level=2)

print("ToolAgent:", agent.run("What's the weather like in Paris?"))

# agent = CodeAgent(tools=[get_weather], model_id=chosen_model_id, verbosity_level=2)

# print("CodeAgent:", agent.run("What's the weather like in Paris?"))
