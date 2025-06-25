import logging
from rich.console import Console
from enum import Enum
from rich.logging import RichHandler
from rich.text import Text
from typing import Optional, Dict, Any
from rich.style import Style
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.theme import Theme

from .common import MessageType

# 定义自定义日志级别
SUCCESS_LEVEL = 25  # 介于 INFO(20) 和 WARNING(30) 之间
SYSTEM_LEVEL = 22
AGENT_LEVEL = 23
TOOL_LEVEL = 24
USER_LEVEL = 21
FAILURE_LEVEL = 35  # 介于 WARNING(30) 和 ERROR(40) 之间

# 注册自定义日志级别
logging.addLevelName(
    SUCCESS_LEVEL, MessageType.SUCCESS.value.upper()
)  # 使用 MessageType 的值作为日志级别名称
logging.addLevelName(SYSTEM_LEVEL, MessageType.SYSTEM.value.upper())
logging.addLevelName(AGENT_LEVEL, MessageType.AGENT.value.upper())
logging.addLevelName(TOOL_LEVEL, MessageType.TOOL.value.upper())
logging.addLevelName(USER_LEVEL, MessageType.USER.value.upper())
logging.addLevelName(FAILURE_LEVEL, MessageType.FAILURE.value.upper())


class RichLoggerConfig:
    """
    Configuration class for rich logging.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RichLoggerConfig, cls).__new__(cls)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self, level: str = "INFO", log_file: str = None):
        """
        Initialize the RichLoggerConfig with a logging level and optional log file.

        :param level: The logging level (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
        :param log_file: Optional path to a log file where logs will be written.
        """
        if self.__initialized:
            return
        self.__initialized = True

        self.level = level
        self.log_file = log_file
        self.console = None
        self.logger = None
        self.rich_handler = None
        self.file_handler = None
        self.configure()

    def configure(
        self,
        level: str = "INFO",
        log_file: Optional[str] = None,
        enable_output: bool = True,
        enable_file: bool = False,
    ) -> None:
        """Configure logging handlers and formatters."""

        self.reset_logger()

        # 将字符串级别转换为数字级别
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)
        self.level = level

        theme = Theme(
            {
                # --- 标准日志级别颜色
                # "logging.level.debug": Style(color="green"),
                # "logging.level.info": Style(color="cyan"),
                # "logging.level.warning": Style(color="yellow"),
                # "logging.level.error": Style(color="red"),
                # "logging.level.critical": Style(color="red", bold=True),
                # --- 自定义日志级别颜色
                "logging.level.success": Style(color="green", bold=True),
                "logging.level.system": Style(color="bright_blue"),
                "logging.level.agent": Style(color="bright_green"),
                "logging.level.tool": Style(color="purple"),
                "logging.level.user": Style(color="bright_white"),
                "logging.level.failure": Style(color="red", bold=True),
                # --- 消息内容样式（用于 markup）
                # "debug": Style(color="green"),  # 绿
                # "info": Style(color="cyan"),  # 青
                # "warning": Style(color="yellow"),  # 黄
                # "error": Style(color="red"),  # 红
                # "critical": Style(color="red", bold=True),  # 红
                "system": Style(color="bright_blue"),  # 浅蓝
                "user": Style(color="bright_white"),  # 浅白
                "agent": Style(color="bright_green"),  # 浅绿
                "tool": Style(color="purple"),  # 紫
                "success": Style(color="green", bold=True),  # 成功
                "failure": Style(color="red", bold=True),  # 失败
            }
        )
        # Rich Console
        self.console = Console(theme=theme)

        # Log Format
        rich_format_pattern = "%(message)s"
        log_format_pattern = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        self.rich_handler = RichHandler(
            console=self.console,
            show_time=False,
            rich_tracebacks=True,
            markup=True,  # 启用 markup 以支持自定义样式标签
        )
        self.rich_handler.setLevel(self.level)
        self.rich_handler.setFormatter(
            logging.Formatter(fmt=rich_format_pattern, datefmt="[%X]")
        )

        self.logger = logging.getLogger()
        self.logger.setLevel(self.level)
        # 清除所有现有的 handlers，避免重复输出
        self.logger.handlers.clear()
        self.logger.addHandler(self.rich_handler)
        # 防止向上传播到父logger，避免重复输出
        self.logger.propagate = False

        if self.log_file and enable_file:
            self.file_handler = logging.FileHandler(
                self.log_file, mode="w", encoding="utf-8"
            )
            self.file_handler.setLevel(self.level)
            self.file_handler.setFormatter(
                logging.Formatter(fmt=log_format_pattern, datefmt="%Y-%m-%d %H:%M:%S")
            )
            self.logger.addHandler(self.file_handler)

    def reset_logger(self) -> None:
        """Reset the logger to its initial state."""
        if self.logger is not None:
            for handler in self.logger.handlers[:]:
                self.logger.removeHandler(handler)
        self.console = None
        self.rich_handler = None
        self.file_handler = None

    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """Get the configured logger."""
        if self.logger is None:
            raise ValueError("Logger has not been configured yet.")
        return logging.getLogger(name)


rich_logger = RichLoggerConfig()


def configure(
    level: str = "INFO",
    log_file: str = None,
    enable_output: bool = True,
    enable_file: bool = False,
) -> None:
    """Configure rich logging with the specified settings."""
    rich_logger.configure(
        level=level,
        log_file=log_file,
        enable_output=enable_output,
        enable_file=enable_file,
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取日志记录器的便捷方法

    参数:
        name: 日志记录器名称

    返回:
        logging.Logger: 日志记录器
    """
    logger = rich_logger.get_logger(name)

    # 添加自定义日志方法
    def success(message, *args, **kwargs):
        logger._log(SUCCESS_LEVEL, f"[success]{message}[/success]", args, **kwargs)

    def system(message, *args, **kwargs):
        logger._log(SYSTEM_LEVEL, f"[system]{message}[/system]", args, **kwargs)

    def agent(message, *args, **kwargs):
        logger._log(AGENT_LEVEL, f"[agent]{message}[/agent]", args, **kwargs)

    def tool(message, *args, **kwargs):
        logger._log(TOOL_LEVEL, f"[tool]{message}[/tool]", args, **kwargs)

    def user(message, *args, **kwargs):
        logger._log(USER_LEVEL, f"[user]{message}[/user]", args, **kwargs)

    def failure(message, *args, **kwargs):
        logger._log(FAILURE_LEVEL, f"[failure]{message}[/failure]", args, **kwargs)

    # 绑定自定义方法到logger对象
    logger.success = success
    logger.system = system
    logger.agent = agent
    logger.tool = tool
    logger.user = user
    logger.failure = failure

    return logger
