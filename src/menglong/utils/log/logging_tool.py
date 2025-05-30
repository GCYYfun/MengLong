"""Rich logging utilities for MengLong.

This module combines the Python logging module with Rich for beautiful and structured logging.
"""

import logging
import sys
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from rich.table import Table
from rich import box

# Create console instance
console = Console()

# Configure logging with Rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, console=console, show_time=False)],
)

# Create logger
logger = logging.getLogger("menglong")


class MessageType(Enum):
    """Message types for different styling."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SYSTEM = "system"
    USER = "user"
    AGENT = "agent"
    DEBUG = "debug"


# Define styles for different message types
STYLES = {
    MessageType.INFO: Style(color="cyan"),
    MessageType.SUCCESS: Style(color="green"),
    MessageType.WARNING: Style(color="yellow"),
    MessageType.ERROR: Style(color="red", bold=True),
    MessageType.SYSTEM: Style(color="bright_blue"),
    MessageType.USER: Style(color="bright_white"),
    MessageType.AGENT: Style(color="bright_green"),
    MessageType.DEBUG: Style(color="bright_black"),
}

# Map MessageType to logging levels
LOG_LEVELS = {
    MessageType.INFO: logging.INFO,
    MessageType.SUCCESS: logging.INFO,
    MessageType.WARNING: logging.WARNING,
    MessageType.ERROR: logging.ERROR,
    MessageType.SYSTEM: logging.INFO,
    MessageType.USER: logging.INFO,
    MessageType.AGENT: logging.INFO,
    MessageType.DEBUG: logging.DEBUG,
}


def print(
    message: Any,
    msg_type: Union[MessageType, str] = MessageType.INFO,
    title: Optional[str] = None,
    use_panel: bool = False,
    log: bool = True,
) -> None:
    """Rich print and log function to replace standard print.

    Args:
        message: The message to print
        msg_type: Type of message (determines styling)
        title: Optional title for the panel
        use_panel: Whether to use a panel for output
        log: Whether to also log the message using the logging module
    """
    # Convert string message type to enum if needed
    if isinstance(msg_type, str):
        try:
            msg_type = MessageType(msg_type)
        except ValueError:
            msg_type = MessageType.INFO

    style = STYLES.get(msg_type, STYLES[MessageType.INFO])

    # Format the message for display
    if use_panel:
        formatted_msg = Panel(
            str(message), title=title, style=style, border_style=style, expand=False
        )
        console.print(formatted_msg)
    else:
        text = Text(str(message), style=style)
        if title:
            title_text = Text(f"{title}: ", style=Style(bold=True))
            text = Text.assemble(title_text, text)
        console.print(text)

    # Also log using the logging module if requested
    if log:
        log_level = LOG_LEVELS.get(msg_type, logging.INFO)
        log_message = f"{title + ': ' if title else ''}{message}"
        logger.log(log_level, log_message)


def print_table(
    data: list, columns: list, title: Optional[str] = None, log: bool = True
) -> None:
    """Print data in a formatted table and optionally log it.

    Args:
        data: List of data rows
        columns: List of column names
        title: Optional title for the table
        log: Whether to also log the table data
    """
    table = Table(box=box.ROUNDED, title=title)

    # Add columns
    for column in columns:
        table.add_column(column, style="cyan")

    # Add rows
    for row in data:
        table.add_row(*[str(item) for item in row])

    console.print(table)

    # Also log using the logging module if requested
    if log and title:
        logger.info(title)
        for i, row in enumerate(data):
            logger.info(f"  {columns[i]}: {', '.join(str(item) for item in row)}")


def print_json(data: Any, title: Optional[str] = None, log: bool = True) -> None:
    """Print JSON data with syntax highlighting and optionally log it.

    Args:
        data: JSON data to print
        title: Optional title
        log: Whether to also log the JSON data
    """
    if title:
        console.print(f"[bold]{title}[/bold]")

    console.print_json(data=data)

    # Also log using the logging module if requested
    if log:
        if title:
            logger.info(title)
        logger.info(str(data))


def print_rule(title: str = "", style: str = "cyan", log: bool = True) -> None:
    """Print a horizontal rule with optional title and optionally log it.

    Args:
        title: Title to include in the rule
        style: Style for the rule
        log: Whether to also log the rule
    """
    console.rule(title, style=style)

    # Also log using the logging module if requested
    if log and title:
        logger.info(f"=== {title} ===")


def configure_logger(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_str: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
) -> None:
    """Configure the logger with custom settings.

    Args:
        level: The logging level (default: INFO)
        log_file: Optional file path to write logs to
        format_str: Format string for log messages
    """
    logger.setLevel(level)

    # Create file handler if log_file is specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(format_str)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)


# Export the logger for direct usage
get_logger = lambda: logger
