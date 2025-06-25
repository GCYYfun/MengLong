from typing import List, Dict, Any, Callable, Optional, Union, Literal
from enum import Enum
import json
import inspect
import asyncio
from enum import Enum, IntEnum, auto


class ToolInfo:
    """工具信息类，存储工具的元数据

    用于封装函数工具的相关信息，包括函数本身、名称、描述和参数规范。
    支持从函数签名自动生成参数规范，包括类型推断和必需参数检测。

    Attributes:
        func (Callable): 被封装的函数对象
        name (str): 工具名称，默认使用函数名
        description (str): 工具描述，默认使用函数的docstring
        parameters (Dict): 参数规范，包含类型、默认值等信息

    Methods:
        _auto_generate_parameters(): 从函数签名自动生成参数规范

    Note:
        当前实现确实没有处理函数参数的描述信息。如果需要参数描述，
        可以考虑解析函数docstring中的参数文档，或者通过其他方式提供。
    """

    def __init__(
        self,
        func: Callable,
        name: str = None,
        description: str = "",
        parameters: Dict = None,
    ):
        self.func = func
        self.name = name or func.__name__
        self.description = description or func.__doc__ or ""
        self.parameters = parameters or self._auto_generate_parameters()

    def _auto_generate_parameters(self) -> Dict:
        """自动从函数签名生成参数规范

        支持的特性：
        - 从类型注解推断参数类型
        - 从默认值推断必需参数
        - 从 docstring 提取参数描述
        - 支持 Literal 类型注解（转换为 enum）
        - 支持嵌套类型（List[str], Dict[str, Any] 等）
        - 为没有描述的参数生成智能后备描述
        """
        sig = inspect.signature(self.func)
        properties = {}
        required = []

        # 尝试从 docstring 解析参数描述
        param_descriptions = self._parse_docstring_params()

        for param_name, param in sig.parameters.items():
            # 跳过 self 参数
            if param_name == "self":
                continue

            param_info = {"type": "string"}  # 默认类型

            # 添加参数描述 （使用 docstring）
            if param_name in param_descriptions:
                param_info["description"] = param_descriptions[param_name]

            # 从类型注解推断类型和其他属性
            if param.annotation != inspect.Parameter.empty:
                param_info.update(self._analyze_type_annotation(param.annotation))

            # 从默认值推断是否必需
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
            else:
                # 处理枚举类型的默认值
                if isinstance(param.default, Enum):
                    param_info["default"] = param.default.value
                else:
                    param_info["default"] = param.default

            properties[param_name] = param_info

        return {"type": "object", "properties": properties, "required": required}

    def _parse_docstring_params(self) -> Dict[str, str]:
        """从函数的 docstring 中解析参数描述

        支持 Google 风格和 NumPy 风格的 docstring
        """
        param_descriptions = {}

        if not self.func.__doc__:
            return param_descriptions

        docstring = self.func.__doc__.strip()
        lines = docstring.split("\n")

        # 查找 Args: 或 Parameters: 部分
        in_args_section = False
        for line in lines:
            line = line.strip()

            # 检测 Args 或 Parameters 部分的开始
            if line.lower().startswith(
                ("args:", "arguments:", "parameters:", "params:")
            ):
                in_args_section = True
                continue

            # 检测其他部分的开始（结束 args 部分）
            if in_args_section and line.endswith(":") and not line.startswith(" "):
                break

            # 解析参数行
            if in_args_section and ":" in line:
                # 支持格式: "param_name: description" 或 "param_name (type): description"
                if line.strip().startswith(("-", "*", "•")):
                    # 列表格式
                    line = line.strip()[1:].strip()

                parts = line.split(":", 1)
                if len(parts) == 2:
                    param_part = parts[0].strip()
                    description = parts[1].strip()

                    # 提取参数名（移除类型信息）
                    if "(" in param_part and ")" in param_part:
                        param_name = param_part.split("(")[0].strip()
                    else:
                        param_name = param_part.strip()

                    param_descriptions[param_name] = description

        return param_descriptions

    def _analyze_type_annotation(self, annotation) -> Dict[str, Any]:
        """分析类型注解并生成相应的参数信息"""
        param_info = {}

        # 处理基本类型
        if annotation == int:
            param_info["type"] = "integer"
        elif annotation == float:
            param_info["type"] = "number"
        elif annotation == bool:
            param_info["type"] = "boolean"
        elif annotation == str:
            param_info["type"] = "string"

        # 处理 Literal 类型（枚举值）
        elif hasattr(annotation, "__origin__") and annotation.__origin__ is Literal:
            param_info["type"] = "string"
            param_info["enum"] = list(annotation.__args__)

        # 处理 Union 类型
        elif hasattr(annotation, "__origin__") and annotation.__origin__ is Union:
            # 简化处理：使用第一个非 None 类型
            for arg in annotation.__args__:
                if arg is not type(None):
                    return self._analyze_type_annotation(arg)

        # 处理 List 类型
        elif hasattr(annotation, "__origin__") and annotation.__origin__ is list:
            param_info["type"] = "array"
            if hasattr(annotation, "__args__") and annotation.__args__:
                item_type = self._analyze_type_annotation(annotation.__args__[0])
                param_info["items"] = item_type

        # 处理 Dict 类型
        elif hasattr(annotation, "__origin__") and annotation.__origin__ is dict:
            param_info["type"] = "object"

        # 处理 Enum 类型
        elif inspect.isclass(annotation) and issubclass(annotation, Enum):
            param_info["type"] = "string"
            param_info["enum"] = [e.value for e in annotation]

        return param_info


# 全局工具注册表
GLOBAL_TOOLS = {}


def tool(func_or_name=None, *, description: str = None, parameters: Dict = None):
    """
    工具装饰器，用于标记函数为可用工具

    支持两种使用方式：
    1. @tool  (不带括号，直接装饰)
    2. @tool() 或 @tool(name="...", description="...")  (带括号，装饰器工厂)

    Args:
        func_or_name: 当直接使用 @tool 时是函数对象，当使用 @tool(...) 时是工具名称或None
        description: 工具描述，默认使用函数文档字符串
        parameters: 工具参数规范，默认自动从函数签名生成

    Usage:
        # 方式1：直接装饰，完全自动
        @tool
        def get_weather(location: str, unit: str = "celsius"):
            '''获取指定位置的天气信息'''
            return {"location": location, "temperature": 22}

        # 方式2：带参数装饰
        @tool()
        def get_weather_auto():
            pass

        # 方式3：指定参数
        @tool(description="获取天气信息")
        def get_weather_custom():
            pass
    """

    def decorator(func: Callable) -> Callable:
        # 如果 func_or_name 是字符串，说明是工具名称
        name = func_or_name if isinstance(func_or_name, str) else None

        # 创建工具信息
        tool_info = ToolInfo(
            func=func, name=name, description=description, parameters=parameters
        )

        # 注册到全局工具表
        tool_name = tool_info.name
        GLOBAL_TOOLS[tool_name] = tool_info

        # 在函数上添加标记
        func._is_tool = True
        func._tool_info = tool_info

        return func

    # 如果 func_or_name 是函数对象，说明是 @tool 直接装饰
    if callable(func_or_name):
        return decorator(func_or_name)

    # 否则是 @tool() 或 @tool(name="...") 形式，返回装饰器
    return decorator


def get_tools_from_module(module_or_namespace) -> Dict[str, ToolInfo]:
    """从模块或命名空间中提取所有用 @tool 装饰的函数"""
    tools = {}

    if hasattr(module_or_namespace, "__dict__"):
        namespace = module_or_namespace.__dict__
    elif isinstance(module_or_namespace, dict):
        namespace = module_or_namespace
    else:
        return tools

    for name, obj in namespace.items():
        if callable(obj) and hasattr(obj, "_is_tool") and hasattr(obj, "_tool_info"):
            tool_info = obj._tool_info
            tools[tool_info.name] = tool_info

    return tools


def get_global_tools() -> Dict[str, ToolInfo]:
    """获取全局注册的所有工具"""
    return GLOBAL_TOOLS.copy()


class ToolManager:
    """工具管理器，负责工具的注册、格式化和执行"""

    def __init__(self):
        """初始化工具管理器"""
        self.curr_tools: List = None  # 工具注册表，存储工具信息
        self.tools = {}  # 工具注册表

    def add_tools(self, tools: List):
        """添加工具到管理器"""
        self.curr_tools = tools
        if isinstance(tools, list):
            for tool in tools:
                tool_info = tool._tool_info
                if isinstance(tool_info, ToolInfo):
                    self.tools[tool_info.name] = {
                        "function": tool_info.func,
                        "description": tool_info.description,
                        "parameters": tool_info.parameters,
                    }
                else:
                    raise ValueError(
                        f"Invalid tool type: {type(tool_info)}. Expected ToolInfo instance."
                    )
        else:
            raise ValueError("Tools must be a list of Tool instances")

    def register_tool(
        self, name: str, func: Callable, description: str = "", parameters: Dict = None
    ):
        """注册工具函数"""
        self.tools[name] = {
            "function": func,
            "description": description,
            "parameters": parameters or {},
        }

    def register_tools_from_functions(self, *functions):
        """从函数列表中注册带有 @tool 装饰器的工具"""
        for func in functions:
            if hasattr(func, "_is_tool") and hasattr(func, "_tool_info"):
                tool_info = func._tool_info
                self.tools[tool_info.name] = {
                    "function": tool_info.func,
                    "description": tool_info.description,
                    "parameters": tool_info.parameters,
                }

    def register_tools_from_module(self, module_or_namespace):
        """从模块或命名空间中自动注册所有用 @tool 装饰的函数"""
        tools = get_tools_from_module(module_or_namespace)
        for tool_name, tool_info in tools.items():
            self.tools[tool_name] = {
                "function": tool_info.func,
                "description": tool_info.description,
                "parameters": tool_info.parameters,
            }

    def register_global_tools(self):
        """注册所有全局注册的工具"""
        global_tools = get_global_tools()
        for tool_name, tool_info in global_tools.items():
            self.tools[tool_name] = {
                "function": tool_info.func,
                "description": tool_info.description,
                "parameters": tool_info.parameters,
            }

    def auto_register_tools(self, tools=None):
        """智能工具注册方法，支持多种输入格式"""
        if tools is None:
            self.register_global_tools()
        elif hasattr(tools, "__dict__") or isinstance(tools, dict):
            self.register_tools_from_module(tools)
        elif isinstance(tools, (list, tuple)):
            if tools and isinstance(tools[0], str):
                global_tools = get_global_tools()
                for tool_name in tools:
                    if tool_name in global_tools:
                        tool_info = global_tools[tool_name]
                        self.tools[tool_name] = {
                            "function": tool_info.func,
                            "description": tool_info.description,
                            "parameters": tool_info.parameters,
                        }
            else:
                self.register_tools_from_functions(*tools)
        else:
            raise ValueError(f"Unsupported tools type: {type(tools)}")

    def format_tools_for_model(self, tools, provider: str) -> List[Dict]:
        """将注册的工具格式化为模型可用的格式"""
        formatted_tools = []
        for name, tool_info in tools.items():
            match provider:
                case "aws":
                    formatted_tools.append(
                        {
                            "toolSpec": {
                                "name": name,
                                "description": tool_info["description"],
                                "inputSchema": {"json": tool_info["parameters"]},
                            }
                        }
                    )
                case "openai" | "deepseek" | "infinigence":
                    formatted_tools.append(
                        {
                            "type": "function",
                            "function": {
                                "name": name,
                                "description": tool_info["description"],
                                "parameters": tool_info["parameters"],
                            },
                        }
                    )
        return formatted_tools

    def format_tool_choice(self, provider: str):
        """根据模型类型格式化tool_choice"""
        match provider:
            case "aws":
                return {"type": "any"}
            case "openai" | "deepseek" | "infinigence":
                return "required"

    def execute_tool_call(self, tool_descriptions) -> List:
        """执行工具调用（同步版本）"""
        tool_results = []
        for tool_call in tool_descriptions:
            tool_name = tool_call.name
            try:
                arguments = (
                    json.loads(tool_call.arguments)
                    if isinstance(tool_call.arguments, str)
                    else tool_call.arguments
                )
            except json.JSONDecodeError:
                arguments = tool_call.arguments

            tool_result = self._execute_tool(tool_name, arguments)
            tool_results.append({"id": tool_call.id, "content": tool_result})

        return tool_results

    async def execute_tool_call_async(self, tool_descriptions) -> List:
        """执行工具调用（异步版本）"""
        tool_results = []
        for tool_call in tool_descriptions:
            tool_name = tool_call.name
            try:
                arguments = (
                    json.loads(tool_call.arguments)
                    if isinstance(tool_call.arguments, str)
                    else tool_call.arguments
                )
            except json.JSONDecodeError:
                arguments = tool_call.arguments

            tool_result = await self._async_execute_tool(tool_name, arguments)
            tool_results.append({"id": tool_call.id, "content": tool_result})

        return tool_results

    def _execute_tool(self, tool_name: str, arguments: Dict) -> str:
        """执行单个工具调用（同步）"""
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' not found"

        try:
            tool_func = self.tools[tool_name]["function"]
            result = tool_func(**arguments)
            return (
                json.dumps(result, ensure_ascii=False)
                if isinstance(result, dict)
                else str(result)
            )
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"

    async def _async_execute_tool(self, tool_name: str, arguments: Dict) -> str:
        """执行单个工具调用（异步）"""
        if tool_name not in self.tools:
            return f"Tool '{tool_name}' not found"

        tool_func = self.tools[tool_name]["function"]

        try:
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**arguments)
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, lambda: tool_func(**arguments)
                )

            return result
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"

    def get_available_tools_description(self) -> str:
        """获取可用工具的描述"""
        if not self.tools:
            return "当前没有可用的工具"

        tool_descriptions = []
        for name, tool in self.tools.items():
            desc = tool.get("description", "无描述")
            tool_descriptions.append(f"- {name}: {desc}")

        return "\n".join(tool_descriptions)
