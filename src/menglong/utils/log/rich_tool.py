"""Rich printing utilities for MengLong - 简洁易用的打印工具."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from .common import MessageType

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.json import JSON
from rich.markdown import Markdown
from rich.progress import Progress, TaskID
from rich.status import Status
from rich.tree import Tree
from rich.rule import Rule
from rich.align import Align
from rich import box

# 全局控制台实例
console = Console()

# 预定义样式
STYLES = {
    MessageType.SUCCESS: "bold green",
    MessageType.ERROR: "bold red",
    MessageType.WARNING: "bold yellow",
    MessageType.INFO: "cyan",
    MessageType.DEBUG: "dim green",
    MessageType.SYSTEM: "bold blue",
    MessageType.USER: "magenta",
    MessageType.AGENT: "bold green",
    MessageType.TOOL: "purple",
}

# 图标映射 - 默认不使用图标
ICONS = {
    MessageType.SUCCESS: "",
    MessageType.ERROR: "",
    MessageType.WARNING: "",
    MessageType.INFO: "",
    MessageType.DEBUG: "",
    MessageType.SYSTEM: "",
    MessageType.USER: "",
    MessageType.AGENT: "",
    MessageType.TOOL: "",
}


def print_message(
    message: str,
    msg_type: MessageType = MessageType.INFO,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    show_icon: bool = False,
    panel: bool = False,
    timestamp: bool = False,
) -> None:
    """
    打印带样式的消息

    Args:
        message: 消息内容
        msg_type: 消息类型
        title: 可选标题
        show_icon: 是否显示图标（默认不显示）
        panel: 是否使用面板包装
        timestamp: 是否显示时间戳
    """
    style = STYLES[msg_type]
    icon = ICONS[msg_type] if show_icon else ""

    # 检测 message 是否为 str
    if not isinstance(message, str):
        message = str(message)

    if panel:
        # 使用面板时，可以使用 markup
        text_parts = []
        if timestamp:
            text_parts.append(f"[dim]{datetime.now().strftime('%H:%M:%S')}[/dim]")
        if icon:
            text_parts.append(icon)
        text_parts.append(message)

        full_message = " ".join(text_parts)

        panel_obj = Panel(
            full_message,
            title=title,
            subtitle=subtitle,
            border_style=style,
            box=box.ROUNDED,
        )
        console.print(panel_obj)
    else:
        # 不使用面板时，构建 Text 对象
        text = Text()

        if timestamp:
            text.append(datetime.now().strftime("%H:%M:%S"), style="dim")
            text.append(" ")
        if icon:
            text.append(icon)
            text.append(" ")
        text.append(message, style=style)

        if title:
            console.print(Text(title, style=style))
        console.print(text)


# 便捷的消息打印函数


def success(message: str, **kwargs) -> None:
    """打印成功消息"""
    print_message(message, MessageType.SUCCESS, **kwargs)


def error(message: str, **kwargs) -> None:
    """打印错误消息"""
    print_message(message, MessageType.ERROR, **kwargs)


def warning(message: str, **kwargs) -> None:
    """打印警告消息"""
    print_message(message, MessageType.WARNING, **kwargs)


def info(message: str, **kwargs) -> None:
    """打印信息消息"""
    print_message(message, MessageType.INFO, **kwargs)


def debug(message: str, **kwargs) -> None:
    """打印调试消息"""
    print_message(message, MessageType.DEBUG, **kwargs)


def system(message: str, **kwargs) -> None:
    """打印系统消息"""
    print_message(message, MessageType.SYSTEM, **kwargs)


def user(message: str, **kwargs) -> None:
    """打印用户消息"""
    print_message(message, MessageType.USER, **kwargs)


def agent(message: str, **kwargs) -> None:
    """打印智能体消息"""
    print_message(message, MessageType.AGENT, **kwargs)


def tool(message: str, **kwargs) -> None:
    """打印工具消息"""
    print_message(message, MessageType.TOOL, **kwargs)


def print_table(
    data: List[Dict[str, Any]],
    headers: Optional[List[str]] = None,
    title: Optional[str] = None,
    show_header: bool = True,
    show_lines: bool = False,
) -> None:
    """
    打印表格

    Args:
        data: 表格数据，字典列表
        title: 表格标题
        headers: 自定义表头，如果不提供则使用第一行的键
        show_header: 是否显示表头
        show_lines: 是否显示行分隔线
    """
    if not data:
        warning("表格数据为空")
        return

    # 获取表头
    if headers is None:
        headers = list(data[0].keys())

    # 创建表格
    table = Table(
        title=title, show_header=show_header, show_lines=show_lines, box=box.SIMPLE_HEAD
    )

    # 添加列
    for header in headers:
        table.add_column(header, style="cyan", no_wrap=True)

    # 添加数据行
    for row in data:
        table.add_row(*[str(row.get(header, "")) for header in headers])

    console.print(table)


def print_json(
    data: Any, title: Optional[str] = None, indent: int = 2, sort_keys: bool = False
) -> None:
    """
    打印格式化的 JSON 数据

    Args:
        data: 要打印的数据
        title: 可选标题
        indent: 缩进空格数
        sort_keys: 是否排序键
    """
    json_obj = JSON.from_data(data, indent=indent, sort_keys=sort_keys)

    if title:
        panel = Panel(json_obj, title=title, border_style="blue")
        console.print(panel)
    else:
        console.print(json_obj)


def print_markdown(markdown: str, title: Optional[str] = None) -> None:
    """
    打印 Markdown 内容

    Args:
        markdown: Markdown 文本
        title: 可选标题
    """
    md = Markdown(markdown)

    if title:
        panel = Panel(md, title=title, border_style="green")
        console.print(panel)
    else:
        console.print(md)


def print_panel(
    content: Union[str, Text],
    title: Optional[str] = None,
    style: str = "blue",
    width: Optional[int] = None,
    padding: int = 1,
) -> None:
    """
    打印面板

    Args:
        content: 面板内容
        title: 面板标题
        style: 边框样式
        width: 面板宽度
        padding: 内边距
    """
    panel = Panel(
        content,
        title=title,
        border_style=style,
        width=width,
        padding=(padding, padding * 2),
        box=box.ROUNDED,
    )
    console.print(panel)


def print_tree(
    data: Dict[str, Any], title: str = "Tree Structure", guide_style: str = "cyan"
) -> None:
    """
    打印树形结构

    Args:
        data: 树形数据
        title: 树标题
        guide_style: 引导线样式
    """
    tree = Tree(title, guide_style=guide_style)

    def add_branch(tree_node: Tree, data_dict: Dict[str, Any]) -> None:
        for key, value in data_dict.items():
            if isinstance(value, dict):
                branch = tree_node.add(f"[bold blue]{key}[/bold blue]")
                add_branch(branch, value)
            elif isinstance(value, list):
                branch = tree_node.add(
                    f"[bold green]{key}[/bold green] ({len(value)} items)"
                )
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        item_branch = branch.add(f"[yellow]Item {i+1}[/yellow]")
                        add_branch(item_branch, item)
                    else:
                        branch.add(f"[white]{item}[/white]")
            else:
                tree_node.add(f"[cyan]{key}:[/cyan] [white]{value}[/white]")

    add_branch(tree, data)
    console.print(tree)


def print_rule(title: str = "", style: str = "blue") -> None:
    """
    打印分隔线

    Args:
        title: 分隔线标题
        style: 线条样式
    """
    console.print(Rule(title, style=style))


def print_status(message: str, spinner: str = "dots") -> Status:
    """
    创建状态指示器

    Args:
        message: 状态消息
        spinner: 旋转器样式

    Returns:
        Status 对象，需要使用 with 语句
    """
    return Status(message, spinner=spinner, console=console)


def print_center(content: Union[str, Text], style: str = "bold") -> None:
    """
    打印居中内容

    Args:
        content: 要居中的内容
        style: 文本样式
    """
    if isinstance(content, str):
        content = Text(content, style=style)
    console.print(Align.center(content))


def print_header(title: str, subtitle: Optional[str] = None) -> None:
    """
    打印标题头部

    Args:
        title: 主标题
        subtitle: 副标题
    """
    print_rule()
    print_center(title, "bold bright_blue")
    if subtitle:
        print_center(subtitle, "dim")
    print_rule()


def print_footer(message: str = "完成") -> None:
    """
    打印页脚

    Args:
        message: 页脚消息
    """
    print_rule()
    print_center(message, "bold green")
    print_rule()


# 便捷的数据打印函数
def print_dict(data: Dict[str, Any], title: str = "数据") -> None:
    """打印字典数据"""
    print_json(data, title)


def print_list(data: List[Any], title: str = "列表") -> None:
    """打印列表数据"""
    if not data:
        warning("列表为空")
        return

    # 如果是字典列表，使用表格
    if data and isinstance(data[0], dict):
        print_table(data, title)
    else:
        # 普通列表用面板显示
        content = "\n".join(f"• {item}" for item in data)
        print_panel(content, title)


def print_separator(char: str = "─", length: int = 50, style: str = "dim") -> None:
    """打印分隔符"""
    console.print(Text(char * length, style=style))


def print_generate(
    generator,
    title: Optional[str] = None,
    show_progress: bool = True,
    style: str = "cyan",
) -> List[Any]:
    """
    打印生成器内容，支持进度显示

    Args:
        generator: 可迭代对象或生成器
        title: 可选标题
        show_progress: 是否显示进度
        style: 文本样式

    Returns:
        生成器产生的所有项目列表
    """
    results = []

    # 如果有标题，先打印标题
    if title:
        print_rule(title, style)

    # 尝试获取长度用于进度条
    try:
        total = len(generator)
        use_progress = show_progress and total > 0
    except (TypeError, AttributeError):
        # 生成器没有长度，使用简单的计数
        total = None
        use_progress = False

    if use_progress and total:
        # 有长度的情况，使用进度条
        with Progress(console=console) as progress:
            task = progress.add_task(f"[{style}]处理中...", total=total)

            for i, item in enumerate(generator):
                results.append(item)
                # 打印当前项
                console.print(f"[{style}]{i+1:>3}.[/{style}] {item}")
                progress.update(task, advance=1)
    else:
        # 无长度或不显示进度的情况
        for i, item in enumerate(generator, 1):
            results.append(item)
            if show_progress:
                # 显示简单的计数
                console.print(f"[{style}]{i:>3}.[/{style}] {item}")
            else:
                console.print(f"[{style}]•[/{style}] {item}")

    if title:
        print_rule(f"完成 ({len(results)} 项)", "green")

    return results


def print_progress(
    tasks: List[Dict[str, Any]], title: Optional[str] = None, show_details: bool = True
) -> None:
    """
    打印多任务进度

    Args:
        tasks: 任务列表，每个任务应包含 'name', 'total', 'completed' 字段
        title: 可选标题
        show_details: 是否显示详细信息

    Example:
        tasks = [
            {"name": "下载文件", "total": 100, "completed": 75},
            {"name": "处理数据", "total": 50, "completed": 30},
        ]
        print_progress(tasks, title="任务进度")
    """
    if title:
        print_rule(title, "blue")

    if not tasks:
        warning("没有任务要显示")
        return

    # 创建进度表格
    progress_data = []

    for task in tasks:
        name = task.get("name", "未知任务")
        total = task.get("total", 0)
        completed = task.get("completed", 0)

        if total > 0:
            percentage = (completed / total) * 100
            progress_bar = "█" * int(percentage // 5) + "░" * (
                20 - int(percentage // 5)
            )
            status = "完成" if completed >= total else "进行中"
        else:
            percentage = 0
            progress_bar = "░" * 20
            status = "等待中"

        progress_data.append(
            {
                "任务": name,
                "进度": progress_bar,
                "百分比": f"{percentage:.1f}%",
                "完成": f"{completed}/{total}",
                "状态": status,
            }
        )

    print_table(progress_data, title="任务进度详情" if show_details else None)

    if show_details:
        # 显示总体统计
        total_tasks = len(tasks)
        completed_tasks = sum(
            1 for task in tasks if task.get("completed", 0) >= task.get("total", 1)
        )

        stats = {
            "总任务数": total_tasks,
            "已完成": completed_tasks,
            "进行中": total_tasks - completed_tasks,
            "总体进度": f"{(completed_tasks/total_tasks)*100:.1f}%",
        }

        print_dict(stats, title="总体统计")


def print_progress_demo() -> None:
    """演示进度条功能"""
    import time

    with Progress(console=console) as progress:
        task = progress.add_task("[cyan]处理中...", total=100)

        while not progress.finished:
            progress.update(task, advance=10)
            time.sleep(0.1)

    success("处理完成!")


# 主要的导出接口
__all__ = [
    # 核心消息函数
    "success",
    "error",
    "warning",
    "info",
    "debug",
    "system",
    "user",
    "agent",
    "tool",
    "print_message",
    # 数据展示函数
    "print_table",
    "print_json",
    "print_markdown",
    "print_dict",
    "print_list",
    # 布局和显示函数
    "print_panel",
    "print_tree",
    "print_rule",
    "print_center",
    "print_header",
    "print_footer",
    "print_separator",
    # 交互功能
    "print_status",
    "print_generate",
    "print_progress",
    "print_progress_demo",
    # 核心对象
    "console",
    "MessageType",
    "STYLES",
    "ICONS",
]
