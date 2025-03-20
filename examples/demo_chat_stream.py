from mlong.model_interface import Model
from mlong.model_interface.utils import user
from mlong.model_interface.schema.response import ChatStreamResponse
model = Model()
res = model.chat(messages=[user("你好,你是谁？简单自我介绍下，100字内。")], model_id="deepseek-reasoner",stream=True)


def stream_response_print(res):
    is_first_reasoning = True
    is_first_text = True


    for item in res:
        if item.message.delta.reasoning_content is not None:
            if is_first_reasoning:
                print("```thinking")
                is_first_reasoning = False

            print(item.message.delta.reasoning_content,end="",flush=True)
        if item.message.delta.text_content is not None:
            if is_first_text:
                print("```")
                print("--------------------------------")
                is_first_text = False

            print(item.message.delta.text_content,end="",flush=True)
        if item.message.finish_reason is not None:
            if item.message.finish_reason == "stop":
                print()

stream_response_print(res)

# print(res)