import os
import sys

# 设置项目根目录, 使得可以直接import mlong
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from mlong.model import Model
from mlong.utils import user, assistant, system

stream_mode = True

client = Model()

prompt = "hello,output 50 word!"

response = client.chat(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    messages=[user(f"{prompt}")],
    temperature=1,
    stream=stream_mode,
    max_tokens=8912,
    thinking={"budget_tokens": 2048, "type": "enabled"},
)
if stream_mode:
    s = response.stream
    if s is not None:
        #     stream_to_str = lambda stream: "".join(
        #         [
        #             (delta.get("text") or delta.get("reasoningContent", {}).get("text", ""))
        #             for event in stream
        #             if "contentBlockDelta" in event
        #             and (delta := event["contentBlockDelta"].get("delta", {}))
        #         ]
        #     )
        #     result = stream_to_str(s)
        #     print(result)
        for event in s:
            if "messageStart" in event:
                print(f"\nRole: {event['messageStart']['role']}\n")
            if "contentBlockDelta" in event:
                if "text" in event["contentBlockDelta"]["delta"]:
                    print(event["contentBlockDelta"]["delta"]["text"], end="")
                if "reasoningContent" in event["contentBlockDelta"]["delta"]:
                    if (
                        "text"
                        in event["contentBlockDelta"]["delta"]["reasoningContent"]
                    ):
                        print(
                            event["contentBlockDelta"]["delta"]["reasoningContent"][
                                "text"
                            ],
                            end="",
                        )
                    if (
                        "signature"
                        in event["contentBlockDelta"]["delta"]["reasoningContent"]
                    ):
                        print("\n--------------------------------\n")
            if "messageStop" in event:
                print(f"\nStop reason: {event['messageStop']['stopReason']}")

else:
    print("----------问题----------")
    print(f"{prompt}")
    print("----------思考----------")
    print(response.choices[0].message.reasoning_content)
    print("----------回复----------")
    print(response.choices[0].message.content)


# 反思

"""
    client 的作用是模型的一个抽象, 通过 client 可以调用不同的模型, 但是 client 本身并不关心模型的实现细节, 只关心模型的调用方式.
    client 通过配置文件来初始化模型, 通过 chat 方法来调用模型.
    chat 方法中, 通过 model 参数来指定模型, 通过 messages 参数来指定输入, 通过 kwargs 参数来指定模型的参数.

    所以 client 在这个包里改名 model call 会好一些,
    因为 
    1. client 的视角是直接为用户使用所定义的,而目前我希望在他做底层支撑,为构建agent框架提供支持.
    2. model call 更能体现他的作用,即调用模型. 也是更系统的视角

    所以 接口类 就 定义为 Model, 行为是 Call
    Model 类中，有一个 chat 方法，用来调用模型
    是一个集成类，用来调用不同的模型
    Model 类中，分为几部分
    1. 配置部分
    2. 实例化部分
    3. 接口调用部分 (model call)

    如何使用
    1. 实例化 Model
    
    mc = Model(configs={})

    2. 调用模型

    设计初衷:
        希望直接使用模型的名字来调用, 所以 model 参数应该是一个字符串, 用来指定模型的名字
        messages 参数是一个列表, 用来指定输入, 每个元素是一个字典, 包含 role 和 content 两个字段
        kwargs 参数是一个字典, 用来指定模型的参数

        模型的名字 要与 provider 的名字相对应, 用 / 分隔, 如 aws/us.anthropic.claude-3-5-sonnet-20241022-v2:0
        但这好像不是很方便,最好能自动映射
        通过名字就知道是哪个 provider, 但是这个名字要怎么映射到 provider 呢?
        所以还是都支持最好

    mc.chat(
        model="aws.us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        messages=[utils.build_a_user_message("hello")],
        temperature=0.5,
    )   
    
    mc.embed(
        model="aws.us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        messages=[utils.build_a_user_message("hello")],
        temperature=0.5,
    )

    3. 类型和工具

    3.1 类型
        Embed 类型
        ChatResponse 类型
        EmbedResponse 类型
    
    3.2 utils 模块
        system
        user
        assistant

"""
