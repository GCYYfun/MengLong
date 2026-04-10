import inspect
import functools
import re
from typing import Any, Dict, List, Optional, get_type_hints, Callable, Union
from menglong.schemas.tool import ToolInfo, FunctionInfo


def _python_type_to_json_type(py_type: Any) -> str:
    """将 Python 类型转换为 JSON Schema 类型"""
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        Any: "string",  # 兜底
    }

    # 获取原始类型 (处理 Optional, Union 等)
    origin = getattr(py_type, "__origin__", None)
    if origin is Union:
        # 取第一个非 None 类型
        args = py_type.__args__
        non_none = [a for a in args if a is not type(None)]
        if non_none:
            return _python_type_to_json_type(non_none[0])

    return type_map.get(py_type, "string")


def _parse_docstring(doc: str) -> Dict[str, str]:
    """从 Docstring 中简单解析参数描述 (Args: 风格)"""
    param_descriptions = {}
    if not doc:
        return param_descriptions

    # 查找 Args: 后的内容
    args_section = re.search(r"Args:\s*(.*)", doc, re.DOTALL | re.IGNORECASE)
    if args_section:
        section_text = args_section.group(1)
        # 匹配 "param_name: description" 格式
        matches = re.findall(r"\s*(\w+):\s*(.*)", section_text)
        for name, desc in matches:
            # 清理换行和空白
            param_descriptions[name] = desc.split("\n")[0].strip()

    return param_descriptions


def tool(func: Callable) -> Callable:
    """
    MengLong Tool 装饰器。
    将一个普通的 Python 函数转换为具备自动导出 Schema 能力的工具对象。
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    # 获取内省信息
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    doc_params = _parse_docstring(func.__doc__ or "")

    # 提取描述 (第一行作为总描述)
    description = (func.__doc__ or "").strip().split("\n")[0]

    # 构造 Parameters Schema
    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        # 跳过 self 和 cls (针对类方法或实例方法)
        if param_name in ("self", "cls"):
            continue
        # 跳过 *args 和 **kwargs (目前简单实现)
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue

        py_type = type_hints.get(param_name, Any)
        json_type = _python_type_to_json_type(py_type)

        properties[param_name] = {
            "type": json_type,
            "description": doc_params.get(param_name, f"Parameter {param_name}"),
        }

        # 判断是否必填 (无默认值)
        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    # 绑定 schema 方法
    def schema() -> ToolInfo:
        return ToolInfo(
            function=FunctionInfo(
                name=func.__name__,
                description=description,
                parameters={
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            )
        )

    wrapper.schema = schema
    wrapper.__is_menglong_tool__ = True
    return wrapper
