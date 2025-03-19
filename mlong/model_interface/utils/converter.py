
import fastapi_poe as fp
from ..schema.response import ChatResponse, MessageContent, Choice, Usage
class PoeConverter:
    """
    Base class for message converters that are compatible with Poe's API.
    """
    @staticmethod
    def convert_request(messages):
        """Convert MLong messages to Poe-compatible format."""
        poe_messages = []
        for message in messages:    
            poe_messages.append(fp.ProtocolMessage(role=message["role"], content=message["content"]))
        return poe_messages

    @staticmethod
    def normalize_response(response):
        """Normalize Poe response to match MLong's response format."""
        message_content = MessageContent(content=response)
        choice = Choice(message=message_content)
        mlong_response = ChatResponse(choices=[choice])
        return mlong_response


class DeepseekConverter:
    """
    Base class for message converters that are compatible with Deepseek's API.
    """
    @staticmethod
    def convert_request(messages):
        """Convert MLong messages to Deepseek-compatible format."""
        pass

    @staticmethod
    def normalize_response(response):
        """Normalize Deepseek response to match MLong's response format."""
        message_content = MessageContent(content="")
        response_choices = response.choices[0]
        if response_choices.message.reasoning_content is not None:
            message_content.reasoning_content = response_choices.message.reasoning_content
            message_content.content = response_choices.message.content
        else:
            message_content.content = response_choices.message.content
            
        choice = Choice(message=message_content)

        usage = Usage(input_tokens=response.usage.prompt_tokens, output_tokens=response.usage.completion_tokens, total_tokens=response.usage.total_tokens)

        mlong_response = ChatResponse(choices=[choice],model=response.model,usage=usage)
        return mlong_response

class OpenAIConverter:
    """
    Base class for message converters that are compatible with OpenAI's API.
    """

    @staticmethod
    def convert_request(messages):
        """Convert messages to OpenAI-compatible format."""
        transformed_messages = []
        for message in messages:
            tmsg = None
            if isinstance(message, str):
                message_dict = message.model_dump(mode="json")
                message_dict.pop("refusal", None)  # Remove refusal field if present
                tmsg = message_dict
            else:
                tmsg = message
            # Check if tmsg is a dict, otherwise get role attribute
            role = tmsg["role"] if isinstance(tmsg, dict) else tmsg.role

            transformed_messages.append(tmsg)
        return transformed_messages

    @staticmethod
    def normalize_response(response):
        """Normalize OpenAI response to match MLong's response format."""
        message_content = MessageContent(content="")
        response_choices = response.choices[0]
        if response_choices.message.reasoning is not None:
            message_content.reasoning_content = response_choices.message.reasoning
            message_content.content = response_choices.message.content
        else:
            message_content.content = response_choices.message.content
            
        choice = Choice(message=message_content)

        usage = Usage(input_tokens=response.usage.prompt_tokens, output_tokens=response.usage.completion_tokens, total_tokens=response.usage.total_tokens)

        mlong_response = ChatResponse(choices=[choice],model=response.model,usage=usage)
        return mlong_response