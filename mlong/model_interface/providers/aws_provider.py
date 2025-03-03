import boto3
from typing import Union
from ..provider import Provider
from ..utils.message_formatter import format_messages_for_aws
from ..schema.response import ChatResponse, ChatStreamResponse, Choice, MessageContent, StreamChoice, StreamDelta


class AwsProvider(Provider):
    """AWS Bedrock服务提供商适配器
    
    该类使用AWS Bedrock的converse API，为所有支持消息的Amazon Bedrock模型提供统一接口。
    支持的模型包括：
    - anthropic.claude-v2
    - meta.llama3-70b-instruct-v1:0
    - mistral.mixtral-8x7b-instruct-v0:1
    """
    
    provider_name = "aws"

    def __init__(self, config: dict):
        """初始化AWS Bedrock提供商
        
        Args:
            config: 配置信息，包含region、access_key、secret_key等
        """
        super().__init__(config)
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=config.get("region_name"),
            aws_access_key_id=config.get("aws_access_key_id"),
            aws_secret_access_key=config.get("aws_secret_access_key")
        )
        self.inference_parameters = [
            "maxTokens",
            "temperature",
            "topP",
            "stopSequences"
        ]

    def normalize_chat_response(self, response: dict, thinking_mode: bool) -> ChatResponse:
        """将Bedrock API的响应格式标准化为统一格式
        
        Args:
            response: Bedrock API的原始响应
            thinking_mode: 是否启用思考模式
            
        Returns:
            标准化后的ChatResponse对象
        """
        message_content = MessageContent(content="")
        
        if thinking_mode:
            message_content.reasoning_content = response["output"]["message"]["content"][0]["reasoningContent"]["reasoningText"]["text"]
            message_content.content = response["output"]["message"]["content"][1]["text"]
        else:
            message_content.content = response["output"]["message"]["content"][0]["text"]
            
        choice = Choice(message=message_content)
        return ChatResponse(choices=[choice])

    def normalize_stream_response(self, response: dict, thinking_mode: bool) -> ChatStreamResponse:
        """将Bedrock API的流式响应格式标准化为统一格式
        
        Args:
            response: Bedrock API的原始流式响应
            thinking_mode: 是否启用思考模式
            
        Returns:
            标准化后的ChatStreamResponse对象
        """
        # 这里需要根据实际的流式响应格式进行处理
        # 以下是一个基本实现，可能需要根据实际情况调整
        stream_delta = StreamDelta(content=response.get("stream", ""))
        stream_choice = StreamChoice(delta=stream_delta)
        return ChatStreamResponse(choices=[stream_choice])

    def model_call(self, call_param: dict, stream_mode: bool, thinking_mode: bool) -> Union[ChatResponse, ChatStreamResponse]:
        """调用Bedrock API
        
        Args:
            call_param: API调用参数
            stream_mode: 是否使用流式模式
            thinking_mode: 是否启用思考模式
            
        Returns:
            API响应
        """
        if stream_mode:
            response = self.client.converse_stream(**call_param)
            return self.normalize_stream_response(response, thinking_mode)
        else:
            response = self.client.converse(**call_param)
            return self.normalize_chat_response(response, thinking_mode)

    def chat(self, model: str, messages: list, **kwargs) -> Union[ChatResponse, ChatStreamResponse]:
        """执行聊天完成
        
        Args:
            model: 模型标识符
            messages: 聊天消息列表
            **kwargs: 其他参数
            
        Returns:
            聊天响应
        """
        system_message, prompt_messages = format_messages_for_aws(messages)

        inference_config = {}
        additional_model_request_fields = {}

        for key, value in kwargs.items():
            if key == "stream":
                continue
            if key in self.inference_parameters:
                inference_config[key] = value
            else:
                additional_model_request_fields[key] = value

        stream_mode = kwargs.get("stream", False)
        thinking_mode = kwargs.get("thinking", {}).get("type", "disabled") == "enabled"

        call_param = {
            "modelId": model,
            "messages": prompt_messages,
            "system": system_message,
            "inferenceConfig": inference_config,
            "additionalModelRequestFields": additional_model_request_fields
        }
        
        return self.model_call(call_param, stream_mode, thinking_mode)
