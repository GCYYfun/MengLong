"""
基础转换器接口定义，为所有转换器提供通用结构。
"""

import traceback
import inspect
from functools import wraps
from typing import Any, Dict, Optional
from ....utils.log import get_logger, print_json
from ....monitor import log_data_transform, log_tool_call


def trace_converter_method(func):
    """
    转换器方法追踪装饰器
    用于追踪转换器方法的执行过程和异常信息
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # 获取方法名和类名
        method_name = func.__name__
        cls_name = (
            args[0].__class__.__name__
            if args and hasattr(args[0], "__class__")
            else "BaseConverter"
        )
        operation_name = f"{cls_name}.{method_name}"

        # 获取logger
        logger = get_logger(f"converter.{cls_name.lower()}")

        try:
            # 记录方法开始执行
            logger.debug(f"开始执行转换器方法: {operation_name}")
            logger.debug(
                f"方法参数: args_count={len(args)}, kwargs_keys={list(kwargs.keys())}"
            )

            # 记录输入数据（只记录关键信息，避免日志过长）
            if args and len(args) > 1:  # 第一个参数通常是 self 或 cls
                input_data = args[1]
                if hasattr(input_data, "__len__") and hasattr(input_data, "__iter__"):
                    logger.debug(
                        f"输入数据类型: {type(input_data).__name__}, 长度: {len(input_data) if input_data else 0}"
                    )
                else:
                    logger.debug(f"输入数据类型: {type(input_data).__name__}")

            # 执行原方法
            result = func(*args, **kwargs)

            # 记录执行成功
            logger.debug(f"转换器方法执行成功: {operation_name}")
            if result is not None:
                logger.debug(f"输出数据类型: {type(result).__name__}")

            # 记录数据转换监控信息
            log_data_transform(
                transform_type=operation_name,
                input_data={
                    "type": type(args[1]).__name__ if len(args) > 1 else "None"
                },
                output_data={
                    "type": type(result).__name__ if result is not None else "None"
                },
            )

            return result

        except Exception as e:
            # 获取详细的错误信息
            error_type = type(e).__name__
            error_msg = str(e)
            error_trace = traceback.format_exc()

            # 获取调用栈信息
            frame_info = inspect.currentframe()
            call_stack = []
            try:
                while frame_info:
                    file_name = frame_info.f_code.co_filename
                    func_name = frame_info.f_code.co_name
                    line_no = frame_info.f_lineno
                    call_stack.append(f"{file_name}:{func_name}:{line_no}")
                    frame_info = frame_info.f_back
            except:
                pass

            # 记录详细错误信息
            logger.error(f"转换器方法执行失败: {operation_name}")
            logger.error(f"错误类型: {error_type}")
            logger.error(f"错误消息: {error_msg}")
            logger.error(f"错误堆栈: {error_trace}")

            # 在终端输出完整的异常信息
            print(f"\n❌ [{cls_name}] 转换器异常详情:")
            print(f"   方法: {operation_name}")
            print(f"   错误: {error_type}: {error_msg}")
            print("   完整堆栈信息:")
            traceback.print_exc()
            print("-" * 80)

            # 记录工具调用错误
            log_tool_call(
                tool_name=operation_name,
                arguments={"args_count": len(args), "kwargs": list(kwargs.keys())},
                error=f"{error_type}: {error_msg}",
            )

            # 打印详细的调试信息
            error_details = {
                "converter_class": cls_name,
                "method_name": method_name,
                "error_type": error_type,
                "error_message": error_msg,
                "call_stack": call_stack[:5],  # 只显示前5层调用栈
                "input_args_count": len(args),
                "input_kwargs": list(kwargs.keys()),
            }

            print_json(error_details, title=f"转换器错误详情 - {operation_name}")

            # 重新抛出异常，保持原有的异常处理逻辑
            raise e

    return wrapper


class BaseConverter:
    """
    所有转换器的基类，定义通用接口。
    """

    @staticmethod
    @trace_converter_method
    def convert_request(messages):
        """
        将MLong消息转换为特定模型API兼容的格式。

        Args:
            messages: MLong格式的消息列表

        Returns:
            转换后的适用于特定API的消息列表
        """
        raise NotImplementedError("子类必须实现此方法")

    @staticmethod
    @trace_converter_method
    def normalize_response(response):
        """
        将模型特定的响应格式标准化为MLong的响应格式。

        Args:
            response: 模型API的原始响应

        Returns:
            标准化后的MLong格式响应
        """
        raise NotImplementedError("子类必须实现此方法")

    @staticmethod
    def _validate_input_messages(messages, method_name="convert_request"):
        """
        验证输入消息格式

        Args:
            messages: 输入消息
            method_name: 调用此验证的方法名

        Raises:
            ValueError: 输入格式无效时抛出
        """
        logger = get_logger("converter.base")

        if messages is None:
            error_msg = f"{method_name}: 输入消息不能为 None"
            logger.error(error_msg)
            raise ValueError(error_msg)

        if not hasattr(messages, "__iter__"):
            error_msg = f"{method_name}: 输入消息必须是可迭代对象，当前类型: {type(messages).__name__}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            messages_list = list(messages)
        except Exception as e:
            error_msg = f"{method_name}: 无法将输入消息转换为列表: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        if len(messages_list) == 0:
            logger.warning(f"{method_name}: 输入消息列表为空")

        logger.debug(f"{method_name}: 输入消息验证通过，消息数量: {len(messages_list)}")
        return messages_list

    @staticmethod
    def _validate_input_tools(tools, method_name: str):
        """验证输入工具的有效性

        Args:
            tools: 输入工具
            method_name: 调用此验证的方法名

        Raises:
            ValueError: 输入格式无效时抛出
        """
        logger = get_logger("converter.base")

        if tools is None:
            error_msg = f"{method_name}: 输入工具不能为 None"
            logger.error(error_msg)
            raise ValueError(error_msg)

        if not hasattr(tools, "__iter__"):
            error_msg = f"{method_name}: 输入工具必须是可迭代对象，当前类型: {type(tools).__name__}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            tools_list = list(tools)
        except Exception as e:
            error_msg = f"{method_name}: 无法将输入工具转换为列表: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        if len(tools_list) == 0:
            logger.warning(f"{method_name}: 输入工具列表为空")

        logger.debug(f"{method_name}: 验证成功，包含 {len(tools_list)} 个工具")
        return tools_list

    @staticmethod
    def _validate_response(response, method_name="normalize_response"):
        """
        验证响应数据

        Args:
            response: 响应数据
            method_name: 调用此验证的方法名

        Raises:
            ValueError: 响应格式无效时抛出
        """
        logger = get_logger("converter.base")

        if response is None:
            error_msg = f"{method_name}: 响应数据不能为 None"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.debug(
            f"{method_name}: 响应数据验证通过，响应类型: {type(response).__name__}"
        )
        return response
