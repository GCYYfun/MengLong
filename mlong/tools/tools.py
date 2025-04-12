from typing import Dict


class Tool:
    """
    LLM 使用的工具类
    定义工具的函数格式
    由一下组成
    - description:str   函数描述
    - name:str          函数名称
    - input: Dict       函数输入参数
    - output: str       函数返回类型
    """

    description: str
    name: str
    input: Dict
    output: str

    def __init__():
        pass
