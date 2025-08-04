import time
import boto3
import json
from typing import Union

from menglong.utils.log import print_json
from ..provider import Provider
from ..schema.ml_response import (
    ChatResponse,
    ChatStreamResponse,
    EmbedResponse,
)
from .converter.aws_converter import AwsConverter


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
        # 初始化客户端
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=config.get("region_name"),
            aws_access_key_id=config.get("aws_access_key_id"),
            aws_secret_access_key=config.get("aws_secret_access_key"),
        )
        # aws 默认参数
        self.inference_parameters = [
            "maxTokens",
            "temperature",
            "topP",
            "stopSequences",
        ]
        self.converter = AwsConverter()

    def is_reasoning(self, model_id, kwargs):
        """检查给定模型是否支持推理模式"""
        if (
            "claude" in model_id
            and kwargs.get("thinking", {}).get("type", "disabled") == "enabled"
        ):
            return True
        return False

    def chat(
        self, model_id: str, messages: list, **kwargs
    ) -> Union[ChatResponse, ChatStreamResponse]:
        """执行聊天完成

        Args:
            model: 模型标识符
            messages: 聊天消息列表
            **kwargs: 其他参数

        Returns:
            聊天响应
        """
        system_message, prompt_messages = self.converter.convert_request_messages(
            messages
        )
        inference_config = {}
        additional_model_request_fields = {}
        tool_config = {}

        for key, value in kwargs.items():
            if key == "stream":
                continue
            if key == "debug":
                continue
            if key in self.inference_parameters:
                inference_config[key] = value
            elif key == "tools":
                tool_config[key] = self.converter.convert_tools(value, model_id)
            else:
                additional_model_request_fields[key] = value

        stream_mode = kwargs.get("stream", False)
        debug = kwargs.get("debug", False)

        # 设置是否使用推理模式
        AwsConverter.reasoning = self.is_reasoning(model_id, kwargs)

        call_param = {
            "modelId": model_id,
            "messages": prompt_messages,
            "system": system_message,
            "inferenceConfig": inference_config,
            "additionalModelRequestFields": additional_model_request_fields,
        }

        if tool_config and tool_config is not {}:
            call_param["toolConfig"] = tool_config
        # 如果是流式模式，调用流式处理
        if stream_mode:
            response = self.client.converse_stream(**call_param)
            return self.converter.normalize_stream_response(response, debug=debug)
        else:
            response = self.client.converse(**call_param)
            return self.converter.normalize_response(response, debug=debug)

    def embed(self, model_id: str, texts: [], **kwargs) -> EmbedResponse:
        """执行嵌入向量计算

        Args:
            model: 模型标识符
            text: 文本
            **kwargs: 其他参数

        Returns:
            嵌入向量响应
        """
        # print("Model ID: {}".format(model_id))
        # print("Embedding text: {}".format(texts))
        request = {
            "texts": texts,
            "input_type": "search_document",
        }
        request = json.dumps(request)
        # Invoke the model with the request.
        response = self.client.invoke_model(modelId=model_id, body=request)

        # Decode the model's native response body.
        model_response = json.loads(response["body"].read())
        embeddings = model_response["embeddings"]

        return EmbedResponse(embeddings=embeddings, metadata=texts, model=model_id)
