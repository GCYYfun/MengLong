
import fastapi_poe as fp
from ..schema.response import ChatResponse, Content, Usage, Message,ContentDelta, StreamMessage, ChatStreamResponse
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
        content = Content(text_content=response)
        message = Message(message=content)
        mlong_response = ChatResponse(message=message)
        return mlong_response


class DeepseekConverter:
    """
    Base class for message converters that are compatible with Deepseek's API.
    """
    reasoning = False

    @staticmethod
    def convert_request(messages):
        """Convert MLong messages to Deepseek-compatible format."""
        pass

    @staticmethod
    def normalize_response(response):
        """Normalize Deepseek response to match MLong's response format."""
        content = Content(text_content="")
        if DeepseekConverter.reasoning:
            content.reasoning_content = response.choices[0].message.reasoning_content
            content.text_content = response.choices[0].message.content
        else:
            content.text_content = response.choices[0].message.content
            
        message = Message(content=content,finish_reason=response.choices[0].finish_reason)

        usage = Usage(input_tokens=response.usage.prompt_tokens, output_tokens=response.usage.completion_tokens, total_tokens=response.usage.total_tokens)

        mlong_response = ChatResponse(message=message,model=response.model,usage=usage)
        return mlong_response
    
    @staticmethod
    def normalize_stream_response(response_stream):
        """Normalize Deepseek stream response to match MLong's response format."""
        # 返回生成器
        for chunk in response_stream:
            print("chunk:",chunk)
            if chunk.choices:
                if DeepseekConverter.reasoning:
                    delta = ContentDelta(
                        text_content=chunk.choices[0].delta.content,
                        reasoning_content=chunk.choices[0].delta.reasoning_content
                    )
                else:
                    delta = ContentDelta(
                        text_content=chunk.choices[0].delta.content,
                        reasoning_content=None
                    )
                message = StreamMessage(
                    delta=delta,
                    finish_reason=chunk.choices[0].finish_reason
                )
                yield ChatStreamResponse(message=message,model_id=chunk.model)

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
        message_content = Content(text_content="")
        response_choices = response.choices[0]
        if response_choices.message.reasoning is not None:
            message_content.reasoning_content = response_choices.message.reasoning
            message_content.content = response_choices.message.content
        else:
            message_content.content = response_choices.message.content
            
        message = Message(message=message_content)

        usage = Usage(input_tokens=response.usage.prompt_tokens, output_tokens=response.usage.completion_tokens, total_tokens=response.usage.total_tokens)

        mlong_response = ChatResponse(message=message,model=response.model,usage=usage)
        return mlong_response