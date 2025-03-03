import os

import boto3
from mlong.provider import Provider
from mlong.types import ChatResponse, ChatStreamResponse
from mlong.utils import format_messages_for_aws


class AwsProvider(Provider):
    def __init__(self, **config):
        """
        Initialize the AWS Bedrock provider with the given configuration.

        This class uses the AWS Bedrock converse API, which provides a consistent interface
        for all Amazon Bedrock models that support messages. Examples include:
        - anthropic.claude-v2
        - meta.llama3-70b-instruct-v1:0
        - mistral.mixtral-8x7b-instruct-v0:1

        The model value can be a baseModelId for on-demand throughput or a provisionedModelArn
        for higher throughput. To obtain a provisionedModelArn, use the CreateProvisionedModelThroughput API.

        For more information on model IDs, see:
        https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html

        Note:
        - The Anthropic Bedrock client uses default AWS credential providers, such as
          ~/.aws/credentials or the "AWS_SECRET_ACCESS_KEY" and "AWS_ACCESS_KEY_ID" environment variables.
        - If the region is not set, it defaults to us-west-1, which may lead to a
          "Could not connect to the endpoint URL" error.
        - The client constructor does not accept additional parameters.

        Args:
            **config: Configuration options for the provider.

        """
        self.client = boto3.client("bedrock-runtime", region_name=config.get("region"),aws_access_key_id=config.get("access_key"),aws_secret_access_key=config.get("secret_key"))
        self.inference_parameters = [
            "maxTokens",
            "temperature",
            "topP",
            "stopSequences",
        ]

    def normalize_chat_response(self, response, thinking_mode):
        """Normalize the response from the Bedrock API to match OpenAI's response format."""
        norm_response = ChatResponse()
        if thinking_mode:
            norm_response.choices[0].message.reasoning_content = response["output"][
                "message"
            ]["content"][0]["reasoningContent"]["reasoningText"]["text"]
            norm_response.choices[0].message.content = response["output"]["message"][
                "content"
            ][1]["text"]
        else:
            norm_response.choices[0].message.content = response["output"]["message"][
                "content"
            ][0]["text"]
        return norm_response

    def normalize_stream_response(self, response, thinking_mode):
        """Normalize the response from the Bedrock API to match OpenAI's response format."""
        norm_response = ChatStreamResponse()
        # norm_response.id = response["id"]
        stream = response.get("stream")
        norm_response.stream = stream
        # if stream:
        #     print(type(stream))
        #     for event in stream:

        #         if "messageStart" in event:
        #             print(f"\nRole: {event['messageStart']['role']}")

        #         if "contentBlockDelta" in event:
        #             print(event["contentBlockDelta"]["delta"]["text"], end="")

        #         if "messageStop" in event:
        #             print(f"\nStop reason: {event['messageStop']['stopReason']}")

        #         if "metadata" in event:
        #             metadata = event["metadata"]
        #             if "usage" in metadata:
        #                 print("\nToken usage")
        #                 print(f"Input tokens: {metadata['usage']['inputTokens']}")
        #                 print(f":Output tokens: {metadata['usage']['outputTokens']}")
        #                 print(f":Total tokens: {metadata['usage']['totalTokens']}")
        #             if "metrics" in event["metadata"]:
        #                 print(
        #                     f"Latency: {metadata['metrics']['latencyMs']} milliseconds"
        #                 )
        # norm_response = ChatResponse()
        # norm_response.choices[0].message.content = response["output"]["message"][
        #     "content"
        # ][0]["text"]
        return norm_response

    def model_call(self, call_param, stream_mode, thinking_mode):
        if stream_mode:
            # Call the Bedrock Converse API with the stream parameter.
            response = self.client.converse_stream(**call_param)
            return self.normalize_stream_response(response, thinking_mode)
        else:
            # Call the Bedrock Converse API.
            response = self.client.converse(**call_param)
            return self.normalize_chat_response(response, thinking_mode)

    def chat(self, model, messages, **kwargs):
        # Any exception raised by Anthropic will be returned to the caller.
        # Maybe we should catch them and raise a custom LLMError.
        # https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html
        system_message, prompot_mesages = format_messages_for_aws(messages)

        # Maintain a list of Inference Parameters which Bedrock supports.
        # These fields need to be passed using inferenceConfig.
        # Rest all other fields are passed as additionalModelRequestFields.
        inference_config = {}
        additional_model_request_fields = {}

        # Iterate over the kwargs and separate the inference parameters and additional model request fields.
        for key, value in kwargs.items():
            # 排除 stream 参数
            if key == "stream":
                continue

            if key in self.inference_parameters:
                inference_config[key] = value
            else:
                additional_model_request_fields[key] = value

        # check spicial mode like stream 、 thinking
        stream_mode = kwargs.get("stream", False)
        thinking_mode = (
            True
            if kwargs.get("thinking", {}).get("type", "disabled") == "enabled"
            else False
        )

        # model call
        # call param
        call_param = {
            "modelId": model,  # baseModelId or provisionedModelArn
            "messages": prompot_mesages,
            "system": system_message,
            "inferenceConfig": inference_config,
            "additionalModelRequestFields": additional_model_request_fields,
        }
        return self.model_call(call_param, stream_mode, thinking_mode)
