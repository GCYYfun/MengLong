from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field

class FunctionInfo(BaseModel):
    """函数定义信息"""
    name: str
    description: str
    parameters: Dict[str, Any]

class ToolInfo(BaseModel):
    """
    MengLong 标准工具定义。
    此结构旨在作为通用适配层，各 Provider 会根据此对象生成各自所需的特定格式。
    """
    type: str = "function"
    function: FunctionInfo
