import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import heapq

from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import TextArea, Frame
from prompt_toolkit.filters import has_focus


class Priority(Enum):
    """任务优先级枚举"""

    CRITICAL = 0  # 最高优先级，可以打断其他任务
    HIGH = 1  # 高优先级
    NORMAL = 2  # 普通优先级
    LOW = 3  # 低优先级


class TaskState(Enum):
    """任务状态枚举"""

    UNUSED = "UNUSED"  # 默认初始化
    READY = "READY"  # 准备就绪（不在运行，但随时可以被调度运行）
    RUNNING = "RUNNING"  # 运行中（当前任务正在运行）
    WAITING = "WAITING"  # 等待状态（当前任务等待，所依赖的任务或子任务运行）
    SUSPENDED = "SUSPENDED"  # 挂起状态（任务尚未执行完毕，但被暂停，需要等待恢复后进入READY状态）
    CANCELED = "CANCELED"  # 已取消（任务被取消，不再进行执行）
    COMPLETED = "COMPLETED"  # 已完成（任务顺利完成）
    ERROR = "ERROR"  # 错误状态（任务出现未知情况，标记为错误状态）


class TaskItem:
    """任务项，用于优先队列"""

    def __init__(self, task_id: str, priority: Priority, data: str, timestamp: float):
        self.task_id = task_id
        self.priority = priority
        self.data = data
        self.timestamp = timestamp
        self.state = TaskState.UNUSED  # 初始状态为UNUSED
        self.cancelled = False

    def __lt__(self, other):
        # 优先级越小越优先，时间戳越小越优先
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.timestamp < other.timestamp

    def set_state(self, new_state: TaskState):
        """设置任务状态"""
        self.state = new_state

    def is_ready(self) -> bool:
        """检查任务是否准备就绪"""
        return self.state == TaskState.READY

    def is_running(self) -> bool:
        """检查任务是否正在运行"""
        return self.state == TaskState.RUNNING

    def is_completed(self) -> bool:
        """检查任务是否已完成"""
        return self.state == TaskState.COMPLETED

    def is_canceled(self) -> bool:
        """检查任务是否已取消"""
        return self.state == TaskState.CANCELED

    def can_be_scheduled(self) -> bool:
        """检查任务是否可以被调度"""
        return self.state in [
            TaskState.UNUSED,
            TaskState.READY,
            TaskState.SUSPENDED,
        ]


class TaskScheduler:
    """任务调度器，支持优先级和打断机制"""

    def __init__(self):
        self.priority_queue = []
        self.running_tasks = {}
        self.suspend_tasks = set()  # 挂起的任务集合
        self.completed_tasks = {}
        self.cancelled_tasks = set()
        self.scheduler_running = False

    async def start(self):
        """启动调度器"""
        if not self.scheduler_running:
            self.scheduler_running = True
            asyncio.create_task(self._scheduler_loop())

    async def stop(self):
        """停止调度器"""
        self.scheduler_running = False
        # 取消所有运行中的任务
        for task in self.running_tasks.values():
            if not task.done():
                task.cancel()

    def add_task(self, task_id: str, priority: Priority, data: str) -> TaskItem:
        """添加任务到调度队列"""
        task_item = TaskItem(task_id, priority, data, asyncio.get_event_loop().time())
        task_item.set_state(TaskState.READY)  # 任务添加时设置为READY状态
        heapq.heappush(self.priority_queue, task_item)
        return task_item

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        # 标记队列中的任务为已取消
        for item in self.priority_queue:
            if item.task_id == task_id:
                item.cancelled = True
                item.set_state(TaskState.CANCELED)
                self.cancelled_tasks.add(task_id)
                break

        # 取消正在运行的任务
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            if not task.done():
                task.cancel()
                # 获取任务数据并设置状态
                task_data = getattr(task, "_task_data", None)
                if task_data:
                    task_data.set_state(TaskState.CANCELED)
                self.cancelled_tasks.add(task_id)
                return True

        return task_id in self.cancelled_tasks

    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        return {
            "queue_size": len(
                [item for item in self.priority_queue if not item.cancelled]
            ),
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len(self.completed_tasks),
            "cancelled_tasks": len(self.cancelled_tasks),
        }

    def suspend_task(self, task_id: str) -> bool:
        """挂起任务"""
        # 挂起正在运行的任务
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            if not task.done():
                task.cancel()
                # 获取任务数据并设置状态为挂起
                task_data = getattr(task, "_task_data", None)
                if task_data:
                    task_data.set_state(TaskState.SUSPENDED)
                    # 将任务重新加入队列，等待恢复
                    heapq.heappush(self.priority_queue, task_data)
                del self.running_tasks[task_id]
                return True

        # 挂起队列中的任务
        for item in self.priority_queue:
            if item.task_id == task_id and not item.cancelled:
                item.set_state(TaskState.SUSPENDED)
                return True

        return False

    def resume_task(self, task_id: str) -> bool:
        """恢复挂起的任务"""
        for item in self.priority_queue:
            if item.task_id == task_id and item.state == TaskState.SUSPENDED:
                item.set_state(TaskState.READY)
                return True
        return False

    def get_task_by_id(self, task_id: str) -> Optional[TaskItem]:
        """根据ID获取任务项"""
        # 检查运行中的任务
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            return getattr(task, "_task_data", None)

        # 检查队列中的任务
        for item in self.priority_queue:
            if item.task_id == task_id:
                return item

        # 检查已完成的任务（需要从completed_tasks中获取）
        return None

    async def _scheduler_loop(self):
        """调度器主循环"""
        while self.scheduler_running:
            await asyncio.sleep(0.1)  # 检查间隔

            # 处理高优先级任务的打断逻辑
            if self.priority_queue:
                next_task = self.priority_queue[0]
                if not next_task.cancelled:
                    await self._handle_priority_interruption(next_task)

            # 启动新任务
            await self._start_pending_tasks()

            # 清理已完成的任务
            self._cleanup_completed_tasks()

    async def _handle_priority_interruption(self, next_task: TaskItem):
        """处理优先级打断逻辑"""
        if next_task.priority == Priority.CRITICAL:
            # 关键任务可以打断所有其他任务
            await self._interrupt_lower_priority_tasks(next_task.priority)
        elif next_task.priority == Priority.HIGH and len(self.running_tasks) > 2:
            # 高优先级任务在有多个运行任务时可以打断低优先级任务
            await self._interrupt_lower_priority_tasks(next_task.priority)

    async def _interrupt_lower_priority_tasks(self, priority: Priority):
        """打断低优先级任务"""
        tasks_to_cancel = []
        for task_id, task in self.running_tasks.items():
            task_data = getattr(task, "_task_data", None)
            if task_data and hasattr(task_data, "priority"):
                if task_data.priority.value > priority.value:
                    tasks_to_cancel.append(task_id)

        for task_id in tasks_to_cancel:
            self.cancel_task(task_id)

    async def _start_pending_tasks(self):
        """启动待处理的任务"""
        max_concurrent = 3  # 最大并发任务数

        while (
            len(self.running_tasks) < max_concurrent
            and self.priority_queue
            and not self.priority_queue[0].cancelled
            and self.priority_queue[0].can_be_scheduled()
        ):

            task_item = heapq.heappop(self.priority_queue)
            if not task_item.cancelled and task_item.can_be_scheduled():
                # 设置任务状态为运行中
                task_item.set_state(TaskState.RUNNING)
                # 创建并启动任务
                task = asyncio.create_task(self._execute_task(task_item))
                task._task_data = task_item  # 附加任务数据
                self.running_tasks[task_item.task_id] = task

    async def _execute_task(self, task_item: TaskItem) -> Dict[str, Any]:
        """执行具体任务"""
        start_time = datetime.now()
        try:
            # 根据优先级设置不同的处理时间
            processing_time = {
                Priority.CRITICAL: 1,
                Priority.HIGH: 3,
                Priority.NORMAL: 5,
                Priority.LOW: 8,
            }.get(task_item.priority, 5)

            await asyncio.sleep(processing_time)

            # 设置任务状态为已完成
            task_item.set_state(TaskState.COMPLETED)

            result = {
                "task_id": task_item.task_id,
                "status": "completed",
                "state": task_item.state.value,
                "data": task_item.data,
                "priority": task_item.priority.name,
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "result": f"处理完成: {task_item.data} (优先级: {task_item.priority.name})",
            }

            self.completed_tasks[task_item.task_id] = result
            return result

        except asyncio.CancelledError:
            # 设置任务状态为已取消
            task_item.set_state(TaskState.CANCELED)

            result = {
                "task_id": task_item.task_id,
                "status": "cancelled",
                "state": task_item.state.value,
                "data": task_item.data,
                "priority": task_item.priority.name,
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "result": f"任务被取消: {task_item.data}",
            }
            self.cancelled_tasks.add(task_item.task_id)
            return result

        except Exception as e:
            # 设置任务状态为错误
            task_item.set_state(TaskState.ERROR)

            result = {
                "task_id": task_item.task_id,
                "status": "failed",
                "state": task_item.state.value,
                "data": task_item.data,
                "priority": task_item.priority.name,
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "error": str(e),
            }
            return result

    def _cleanup_completed_tasks(self):
        """清理已完成的任务"""
        completed_task_ids = []
        for task_id, task in self.running_tasks.items():
            if task.done():
                completed_task_ids.append(task_id)

        for task_id in completed_task_ids:
            del self.running_tasks[task_id]


class AsyncTaskManager:
    def __init__(self):
        self.tasks: Dict[str, Any] = {}
        self.task_counter = 0
        self.scheduler = TaskScheduler()

    async def start_scheduler(self):
        """启动调度器"""
        await self.scheduler.start()

    async def stop_scheduler(self):
        """停止调度器"""
        await self.scheduler.stop()

    async def send_task(
        self, task_data: str, priority: Priority = Priority.NORMAL
    ) -> str:
        """发送任务到调度器"""
        self.task_counter += 1
        task_id = f"task_{self.task_counter}"

        # 存储任务信息
        self.tasks[task_id] = {
            "data": task_data,
            "priority": priority.name,
            "status": "queued",
            "state": TaskState.READY.value,
            "created_at": datetime.now().isoformat(),
        }

        # 添加到调度队列
        self.scheduler.add_task(task_id, priority, task_data)
        return task_id

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        success = self.scheduler.cancel_task(task_id)
        if success and task_id in self.tasks:
            self.tasks[task_id]["status"] = "cancelled"
            self.tasks[task_id]["cancelled_at"] = datetime.now().isoformat()
        return success

    def suspend_task(self, task_id: str) -> bool:
        """挂起任务"""
        success = self.scheduler.suspend_task(task_id)
        if success and task_id in self.tasks:
            self.tasks[task_id]["state"] = TaskState.SUSPENDED.value
            self.tasks[task_id]["suspended_at"] = datetime.now().isoformat()
        return success

    def resume_task(self, task_id: str) -> bool:
        """恢复挂起的任务"""
        success = self.scheduler.resume_task(task_id)
        if success and task_id in self.tasks:
            self.tasks[task_id]["state"] = TaskState.READY.value
            self.tasks[task_id]["resumed_at"] = datetime.now().isoformat()
        return success

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        base_status = self.tasks.get(task_id, {"status": "not_found"})

        # 检查调度器中的状态
        if task_id in self.scheduler.completed_tasks:
            completed_task = self.scheduler.completed_tasks[task_id]
            base_status.update(completed_task)
        elif task_id in self.scheduler.running_tasks:
            base_status["status"] = "running"
            base_status["state"] = TaskState.RUNNING.value
            # 获取运行中任务的详细状态
            task = self.scheduler.running_tasks[task_id]
            task_data = getattr(task, "_task_data", None)
            if task_data:
                base_status["state"] = task_data.state.value
        elif task_id in self.scheduler.cancelled_tasks:
            base_status["status"] = "cancelled"
            base_status["state"] = TaskState.CANCELED.value
        else:
            # 检查是否在队列中
            task_item = self.scheduler.get_task_by_id(task_id)
            if task_item:
                base_status["state"] = task_item.state.value
                if task_item.state == TaskState.READY:
                    base_status["status"] = "queued"
                elif task_item.state == TaskState.SUSPENDED:
                    base_status["status"] = "suspended"

        return base_status

    def get_scheduler_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return self.scheduler.get_queue_status()

    def get_all_tasks(self) -> Dict[str, Any]:
        """获取所有任务"""
        return self.tasks


class AsyncTerminalApp:
    def __init__(self):
        self.task_manager = AsyncTaskManager()

        # 创建输出和输入区域
        self.output_area = TextArea(
            text="=== 智能任务调度终端 ===\n支持优先级调度和打断机制\n输入 'help' 查看帮助\n\n",
            read_only=True,
            scrollbar=True,
            wrap_lines=True,
        )
        self.input_area = TextArea(
            text="",
            multiline=False,
            wrap_lines=False,
        )

        # 创建布局
        self.root_container = HSplit(
            [
                Frame(self.output_area, title="输出"),
                Frame(self.input_area, title="输入 (Ctrl+C 退出, Enter 发送)"),
            ]
        )

        # 创建键绑定
        self.kb = KeyBindings()
        self._setup_key_bindings()

        # 创建应用
        self.app = Application(
            layout=Layout(self.root_container, focused_element=self.input_area),
            key_bindings=self.kb,
            full_screen=True,
        )

    def _setup_key_bindings(self):
        @self.kb.add("enter", filter=has_focus(self.input_area))
        async def _(event):
            await self._handle_input()

        @self.kb.add("c-c")
        def _(event):
            event.app.exit()

        @self.kb.add("c-l")
        def _(event):
            """Ctrl+L 清空输出"""
            self.output_area.text = ""

    async def _handle_input(self):
        """处理用户输入"""
        command = self.input_area.text.strip()
        self.input_area.text = ""

        if not command:
            return

        self._append_output(f"> {command}")

        try:
            if command.lower() == "help":
                await self._show_help()
            elif command.lower() == "list":
                await self._list_tasks()
            elif command.lower() == "clear":
                self.output_area.text = ""
            elif command.lower() == "scheduler":
                await self._show_scheduler_status()
            elif command.lower() == "demo":
                await self._run_demo()
            elif command.lower() == "demo-states":
                await self._run_state_demo()
            elif command.startswith("status "):
                task_id = command[7:].strip()
                await self._show_task_status(task_id)
            elif command.startswith("cancel "):
                task_id = command[7:].strip()
                await self._cancel_task(task_id)
            elif command.startswith("suspend "):
                task_id = command[8:].strip()
                await self._suspend_task(task_id)
            elif command.startswith("resume "):
                task_id = command[7:].strip()
                await self._resume_task(task_id)
            elif command.startswith("send "):
                await self._parse_send_command(command[5:].strip())
            else:
                # 默认为普通优先级任务
                await self._send_task(command, Priority.NORMAL)
        except Exception as e:
            self._append_output(f"错误: {str(e)}")

    async def _show_help(self):
        """显示帮助信息"""
        help_text = """可用命令:
- send <优先级> <任务内容>  : 发送指定优先级的任务
  优先级: critical, high, normal, low
  例如: send high 重要数据处理
- <任务内容>               : 发送普通优先级任务
- status <任务ID>          : 查看任务状态
- cancel <任务ID>          : 取消任务
- suspend <任务ID>         : 挂起任务
- resume <任务ID>          : 恢复挂起的任务
- list                    : 列出所有任务
- scheduler               : 查看调度器状态
- demo                    : 运行演示，创建各种优先级的示例任务
- demo-states             : 运行状态演示，展示任务状态转换
- clear                   : 清空输出
- help                    : 显示此帮助
- Ctrl+C                  : 退出程序

优先级说明:
- critical: 关键任务，会打断其他所有任务
- high: 高优先级，在系统繁忙时可能打断低优先级任务
- normal: 普通优先级 (默认)
- low: 低优先级

任务状态说明:
- UNUSED: 默认初始化状态
- READY: 准备就绪，等待调度
- RUNNING: 正在运行
- WAITING: 等待依赖任务完成
- SUSPENDED: 已挂起，等待恢复
- CANCELED: 已取消
- COMPLETED: 已完成
- ERROR: 出现错误"""
        self._append_output(help_text)

    async def _parse_send_command(self, command_text: str):
        """解析send命令，提取优先级和任务内容"""
        parts = command_text.split(" ", 1)
        if len(parts) == 1:
            # 没有指定优先级，使用默认普通优先级
            await self._send_task(parts[0], Priority.NORMAL)
            return

        priority_str, task_data = parts
        priority_map = {
            "critical": Priority.CRITICAL,
            "high": Priority.HIGH,
            "normal": Priority.NORMAL,
            "low": Priority.LOW,
        }

        priority = priority_map.get(priority_str.lower())
        if priority is None:
            # 第一个词不是优先级，整个作为任务内容
            await self._send_task(command_text, Priority.NORMAL)
        else:
            await self._send_task(task_data, priority)

    async def _send_task(self, task_data: str, priority: Priority = Priority.NORMAL):
        """发送任务"""
        if not task_data:
            self._append_output("错误: 任务内容不能为空")
            return

        self._append_output(f"正在发送任务: {task_data} (优先级: {priority.name})")

        try:
            task_id = await self.task_manager.send_task(task_data, priority)
            self._append_output(f"任务已发送, ID: {task_id}")

            # 启动状态监控
            asyncio.create_task(self._monitor_task(task_id))

        except Exception as e:
            self._append_output(f"发送任务失败: {str(e)}")

    async def _cancel_task(self, task_id: str):
        """取消任务"""
        if not task_id:
            self._append_output("错误: 请指定任务ID")
            return

        success = self.task_manager.cancel_task(task_id)
        if success:
            self._append_output(f"任务 {task_id} 已取消")
        else:
            self._append_output(f"无法取消任务 {task_id} (可能不存在或已完成)")

    async def _suspend_task(self, task_id: str):
        """挂起任务"""
        if not task_id:
            self._append_output("错误: 请指定任务ID")
            return

        success = self.task_manager.suspend_task(task_id)
        if success:
            self._append_output(f"任务 {task_id} 已挂起")
        else:
            self._append_output(f"无法挂起任务 {task_id} (可能不存在或无法挂起)")

    async def _resume_task(self, task_id: str):
        """恢复挂起的任务"""
        if not task_id:
            self._append_output("错误: 请指定任务ID")
            return

        success = self.task_manager.resume_task(task_id)
        if success:
            self._append_output(f"任务 {task_id} 已恢复")
        else:
            self._append_output(f"无法恢复任务 {task_id} (可能不存在或不是挂起状态)")

    async def _show_scheduler_status(self):
        """显示调度器状态"""
        status = self.task_manager.get_scheduler_status()
        status_text = f"""调度器状态:
- 队列中任务: {status['queue_size']}
- 运行中任务: {status['running_tasks']}
- 已完成任务: {status['completed_tasks']}
- 已取消任务: {status['cancelled_tasks']}"""
        self._append_output(status_text)

    async def _monitor_task(self, task_id: str):
        """监控任务状态并实时更新"""
        last_status = "unknown"
        last_state = None

        while True:
            await asyncio.sleep(0.5)  # 更频繁的检查
            status_info = self.task_manager.get_task_status(task_id)
            current_status = status_info.get("status", "unknown")
            current_state = status_info.get("state", "UNKNOWN")

            # 只在状态变化时输出
            if current_status != last_status or current_state != last_state:
                if current_status == "running":
                    priority = status_info.get("priority", "NORMAL")
                    self._append_output(
                        f"📋 任务 {task_id} 开始执行 (优先级: {priority}, 状态: {current_state})"
                    )
                elif current_status == "completed":
                    result = status_info.get("result", "未知结果")
                    self._append_output(f"✅ 任务 {task_id} 已完成: {result}")
                    break
                elif current_status == "cancelled":
                    self._append_output(
                        f"❌ 任务 {task_id} 已取消 (状态: {current_state})"
                    )
                    break
                elif current_status == "failed":
                    error = status_info.get("error", "未知错误")
                    self._append_output(
                        f"💥 任务 {task_id} 执行失败: {error} (状态: {current_state})"
                    )
                    break
                elif current_status == "suspended":
                    self._append_output(
                        f"⏸️ 任务 {task_id} 已挂起 (状态: {current_state})"
                    )
                elif current_status == "queued" and current_state == "READY":
                    if last_state == "SUSPENDED":
                        self._append_output(f"▶️ 任务 {task_id} 已恢复，等待执行")

                last_status = current_status
                last_state = current_state

            # 如果任务不存在或已结束，停止监控
            if current_status in ["completed", "cancelled", "failed", "not_found"]:
                break

    async def _show_task_status(self, task_id: str):
        """显示任务状态"""
        status = self.task_manager.get_task_status(task_id)
        if status["status"] == "not_found":
            self._append_output(f"任务 {task_id} 不存在")
        else:
            status_text = json.dumps(status, indent=2, ensure_ascii=False)
            self._append_output(f"任务 {task_id} 状态:\n{status_text}")

    async def _list_tasks(self):
        """列出所有任务"""
        tasks = self.task_manager.get_all_tasks()
        if not tasks:
            self._append_output("暂无任务")
            return

        # 获取调度器状态
        scheduler_status = self.task_manager.get_scheduler_status()

        self._append_output("=== 任务列表 ===")
        self._append_output(
            f"📊 队列: {scheduler_status['queue_size']} | 运行: {scheduler_status['running_tasks']} | 完成: {scheduler_status['completed_tasks']} | 取消: {scheduler_status['cancelled_tasks']}"
        )
        self._append_output("")

        # 按状态分组显示任务
        status_groups = {}
        for task_id, task_info in tasks.items():
            current_status = self.task_manager.get_task_status(task_id)
            status = current_status.get("status", "unknown")
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append((task_id, task_info, current_status))

        # 状态图标映射
        status_icons = {
            "queued": "⏳",
            "running": "🔄",
            "completed": "✅",
            "cancelled": "❌",
            "failed": "💥",
            "suspended": "⏸️",
        }

        # 状态图标映射
        state_icons = {
            "UNUSED": "🔘",
            "READY": "⏳",
            "RUNNING": "🔄",
            "WAITING": "⏱️",
            "SUSPENDED": "⏸️",
            "CANCELED": "❌",
            "COMPLETED": "✅",
            "ERROR": "💥",
        }

        # 按优先级显示各状态的任务
        for status, tasks_list in status_groups.items():
            if tasks_list:
                icon = status_icons.get(status, "❓")
                self._append_output(f"{icon} {status.upper()}:")
                for task_id, task_info, current_status in tasks_list:
                    priority = task_info.get("priority", "NORMAL")
                    data = task_info.get("data", "")
                    state = current_status.get("state", "UNKNOWN")
                    state_icon = state_icons.get(state, "❓")
                    created_time = (
                        task_info.get("created_at", "")[:19]
                        if task_info.get("created_at")
                        else ""
                    )
                    self._append_output(
                        f"  • {task_id} [{priority}] {state_icon} {state} - {data} ({created_time})"
                    )
                self._append_output("")

    async def _run_demo(self):
        """运行演示，创建各种优先级的任务"""
        self._append_output("🎯 开始演示 - 创建不同优先级的任务...")

        demo_tasks = [
            (Priority.LOW, "低优先级：数据备份"),
            (Priority.LOW, "低优先级：日志清理"),
            (Priority.NORMAL, "普通任务：用户数据处理"),
            (Priority.NORMAL, "普通任务：报表生成"),
            (Priority.HIGH, "高优先级：系统监控"),
            (Priority.CRITICAL, "关键任务：安全检查"),
        ]

        created_tasks = []
        for priority, task_data in demo_tasks:
            task_id = await self.task_manager.send_task(task_data, priority)
            created_tasks.append(task_id)
            self._append_output(f"  📝 创建任务 {task_id}: {task_data}")
            await asyncio.sleep(0.5)  # 延迟创建，便于观察调度过程

        self._append_output(f"✨ 演示完成！创建了 {len(created_tasks)} 个任务")
        self._append_output(
            "💡 使用 'list' 命令查看任务状态，'scheduler' 查看调度器状态"
        )

        # 启动所有任务的监控
        for task_id in created_tasks:
            asyncio.create_task(self._monitor_task(task_id))

    async def _run_state_demo(self):
        """运行状态演示，展示任务状态转换"""
        self._append_output("🎭 开始状态演示 - 展示任务状态转换...")

        # 创建几个测试任务
        self._append_output("1️⃣ 创建测试任务...")
        task1_id = await self.task_manager.send_task("状态演示任务1", Priority.NORMAL)
        task2_id = await self.task_manager.send_task("状态演示任务2", Priority.LOW)
        task3_id = await self.task_manager.send_task("状态演示任务3", Priority.HIGH)

        self._append_output(f"   创建了任务: {task1_id}, {task2_id}, {task3_id}")

        # 启动监控
        for task_id in [task1_id, task2_id, task3_id]:
            asyncio.create_task(self._monitor_task(task_id))

        await asyncio.sleep(1)

        # 演示挂起和恢复
        self._append_output("2️⃣ 演示挂起操作...")
        await asyncio.sleep(2)
        await self._suspend_task(task2_id)

        await asyncio.sleep(3)
        self._append_output("3️⃣ 演示恢复操作...")
        await self._resume_task(task2_id)

        await asyncio.sleep(2)
        self._append_output("4️⃣ 演示取消操作...")
        await self._cancel_task(task3_id)

        self._append_output("🎭 状态演示完成！")
        self._append_output("💡 使用 'list' 命令查看任务状态变化")

    def _append_output(self, text: str):
        """添加输出文本"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        new_text = f"[{timestamp}] {text}\n"

        # 添加文本并滚动到底部
        self.output_area.read_only = False
        self.output_area.text += new_text
        self.output_area.buffer.cursor_position = len(self.output_area.text)
        self.output_area.read_only = True

    async def run(self):
        """运行应用"""
        # 启动调度器
        await self.task_manager.start_scheduler()
        self._append_output("调度器已启动，支持优先级任务处理")

        try:
            await self.app.run_async()
        finally:
            # 确保调度器在应用退出时停止
            await self.task_manager.stop_scheduler()
            self._append_output("调度器已停止")


async def main():
    """主函数"""
    app = AsyncTerminalApp()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
