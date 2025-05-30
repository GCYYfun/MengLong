"""Rich printing utilities for MengLong."""

from enum import Enum
from typing import Any, Generator, Optional, Union

from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from rich.table import Table
from rich import box
from rich.live import Live

# Create console instance
console = Console()


class MessageType(Enum):
    """Message types for different styling."""

    INFO = "info"
    DEBUG = "debug"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    FAILURE = "failure"
    SYSTEM = "system"
    USER = "user"
    AGENT = "agent"


# Define styles for different message types
STYLES = {
    MessageType.DEBUG: Style(color="bright_black"),
    MessageType.INFO: Style(color="cyan"),
    MessageType.WARNING: Style(color="yellow"),
    MessageType.ERROR: Style(color="red", bold=True),
    MessageType.SUCCESS: Style(color="green"),
    MessageType.FAILURE: Style(color="bright_red"),
    MessageType.SYSTEM: Style(color="bright_blue"),
    MessageType.USER: Style(color="bright_white"),
    MessageType.AGENT: Style(color="bright_green"),
}


def print(
    message: Any,
    msg_type: Union[MessageType, str] = MessageType.INFO,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    use_panel: bool = False,
    end: str = "\n",
) -> None:
    """Rich print function to replace standard print.

    Args:
        message: The message to print
        msg_type: Type of message (determines styling)
        title: Optional title for the panel
        use_panel: Whether to use a panel for output
    """
    # Convert string message type to enum if needed
    if isinstance(msg_type, str):
        try:
            msg_type = MessageType(msg_type)
        except ValueError:
            msg_type = MessageType.INFO

    style = STYLES.get(msg_type, STYLES[MessageType.INFO])

    if use_panel:
        console.print(
            Panel(
                str(message),
                title=title,
                subtitle=subtitle,
                style=style,
                border_style=style,
                expand=False,
                subtitle_align="left",
            )
        )
    else:
        text = Text(str(message), style=style)
        if title:
            title_text = Text(f"{title}({subtitle}): ", style=Style(bold=True))
            text = Text.assemble(title_text, text)
        console.print(text, end=end)


def print_table(data: list, columns: list, title: Optional[str] = None) -> None:
    """Print data in a formatted table.

    Args:
        data: List of data rows
        columns: List of column names
        title: Optional title for the table
    """
    table = Table(box=box.ROUNDED, title=title)

    # Add columns
    for column in columns:
        table.add_column(column, style="cyan")

    # Add rows
    for row in data:
        table.add_row(*[str(item) for item in row])

    console.print(table)


def print_json(data: Any, title: Optional[str] = None) -> None:
    """Print JSON data with syntax highlighting.

    Args:
        data: JSON data to print
        title: Optional title
    """
    if title:
        console.print(f"[bold]{title}[/bold]")
    console.print_json(data=data)


def print_rule(title: str = "", style: str = "cyan") -> None:
    """Print a horizontal rule with optional title.

    Args:
        title: Title to include in the rule
        style: Style for the rule
    """
    console.rule(title, style=style)


def print_stream(
    message: Generator,
    msg_type: Union[MessageType, str] = MessageType.INFO,
    title: Optional[str] = None,
    use_panel: bool = False,
):
    """Print a stream of messages with optional title and style.

    Args:
        message: Stream messages to print
        msg_type: Type of message (determines styling)
        title: Optional title for the panel
        use_panel: Whether to use a panel for output
    """
    if isinstance(msg_type, str):
        try:
            msg_type = MessageType(msg_type)
        except ValueError:
            msg_type = MessageType.INFO

    style = STYLES.get(msg_type, STYLES[MessageType.INFO])

    if use_panel:
        # Create an empty panel to start with
        panel = Panel("", title=title, style=style, border_style=style, expand=False)

        # Use Live display for streaming updates inside the panel
        with Live(panel, console=console, refresh_per_second=10) as live:
            full_text = ""
            for chunk in message:
                full_text += str(chunk)
                # Update the panel content with each new chunk
                panel = Panel(
                    full_text,
                    title=title,
                    style=style,
                    border_style=style,
                    expand=False,
                )
                live.update(panel)
    else:
        # For non-panel streaming output
        if title:
            title_text = Text(f"{title}: ", style=Style(bold=True))
            console.print(title_text, end="")

        # Stream content directly
        for chunk in message:
            text = Text(str(chunk), style=style)
            console.print(text, end="")
