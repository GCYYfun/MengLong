from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
import uuid
import time
import threading
from collections import deque
import heapq

from menglong.utils.log import (
    print_message,
    print_json,
    print_rule,
)


class TaskStatus(Enum):
    """任务状态枚举"""

    CREATED = "Created"
    PENDING = "Pending"
    READY = "Ready"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELED = "Canceled"


class TaskPriority(Enum):
    """任务优先级"""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class TaskID:
    _id = -1  # 类变量，所有实例共享

    @staticmethod
    def next():
        TaskID._id += 1
        return TaskID._id


class Task:
    """任务描述类 - 定义任务内容"""

    def __init__(
        self,
        prompt: str,
        tools: List[str] = None,
        resources: Dict[str, Any] = None,
        parent_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
    ):
        """
        初始化任务描述
        :param prompt: 任务描述
        :param tools: 可用工具列表
        :param resources: 任务资源
        :param parent_id: 父任务ID
        :param priority: 任务优先级
        """
        # self.task_id = str(uuid.uuid4())
        self.task_id = f"task_{TaskID.next()}"
        self.prompt = prompt
        self.tools = tools or []
        self.resources = resources or {}
        self.parent_id = parent_id
        self.priority = priority
        self.dependencies: List[str] = []  # 任务依赖列表(DAG用)
        self.metadata: Dict[str, Any] = {"created_at": time.time()}

    def add_dependency(self, task_id: str):
        """添加任务依赖"""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)

    def __repr__(self):
        return f"Task({self.task_id[:8]}, '{self.prompt[:20]}...')"


class TCB:
    """任务控制块 (Task Control Block) - 管理任务执行状态"""

    def __init__(self, task: Task):
        """
        初始化任务控制块
        :param task: 关联的任务描述
        """
        self.task_id = task.task_id
        self.task = task
        self.status = TaskStatus.CREATED
        self.result = None
        self.logs: List[str] = []
        self.execution_count = 0  # 执行次数（用于重试）
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.progress = 0.0
        self.worker_id: Optional[str] = None  # 执行任务的worker

    def log(self, message: str):
        """记录任务日志"""
        self.logs.append(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")

    def update_progress(self, progress: float):
        """更新任务进度 (0.0 - 1.0)"""
        self.progress = max(0.0, min(1.0, progress))

    def reset(self):
        """重置任务状态（用于重试）"""
        self.status = TaskStatus.CREATED
        self.result = None
        self.start_time = None
        self.end_time = None
        self.progress = 0.0
        self.execution_count += 1

    def get_execution_time(self) -> float:
        """获取任务执行时间（秒）"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    def __repr__(self):
        return (
            f"TCB({self.task_id[:8]}, {self.status.name}, progress={self.progress:.0%})"
        )


class TaskManager:
    """任务管理器，管理任务树和DAG"""

    def __init__(self):
        self.root_task: Optional[Task] = None
        self.tasks: Dict[str, Task] = {}  # task_id -> Task
        self.tcbs: Dict[str, TCB] = {}  # task_id -> TCB

    def create_task(
        self,
        prompt: str,
        tools: List[str] = None,
        resources: Dict[str, Any] = None,
        parent_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> Tuple[Task, TCB]:
        """创建新任务及其控制块"""
        task = Task(prompt, tools, resources, parent_id, priority)
        tcb = TCB(task)

        self.tasks[task.task_id] = task
        self.tcbs[task.task_id] = tcb

        if parent_id:
            parent = self.tasks.get(parent_id)
            if parent:
                # 在父任务中添加子任务引用
                if "children" not in parent.metadata:
                    parent.metadata["children"] = []
                parent.metadata["children"].append(task.task_id)

        elif not self.root_task:
            self.root_task = task

        tcb.log(f"Task created: {prompt}")
        return task, tcb

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务描述"""
        return self.tasks.get(task_id)

    def get_tcb(self, task_id: str) -> Optional[TCB]:
        """获取任务控制块"""
        return self.tcbs.get(task_id)

    def get_task_tree(self, task_id: str = None) -> Dict:
        """获取任务树结构"""
        task = self.tasks.get(task_id) or self.root_task
        if not task:
            return {}

        def build_tree(node_id: str):
            task = self.tasks[node_id]
            tcb = self.tcbs[node_id]
            return {
                "id": task.task_id,
                "prompt": task.prompt,
                "status": tcb.status.value,
                "progress": tcb.progress,
                "priority": task.priority.name,
                "children": [
                    build_tree(child_id)
                    for child_id in task.metadata.get("children", [])
                ],
            }

        return build_tree(task.task_id) if task else {}

    def get_task_dag(self, root_id: str = None) -> Dict[str, List[str]]:
        """获取任务DAG（有向无环图）"""
        dag = {}
        root_task = self.root_task if root_id is None else self.tasks.get(root_id)

        if not root_task:
            return {}

        # 收集所有相关任务
        all_tasks = self._collect_subtasks(root_task.task_id)

        for task in all_tasks:
            dag[task.task_id] = {
                "dependencies": task.dependencies,
                "dependent_tasks": [
                    t.task_id for t in all_tasks if task.task_id in t.dependencies
                ],
            }
        return dag

    def _collect_subtasks(self, task_id: str) -> List[Task]:
        """收集所有子任务"""
        tasks = []
        if task_id in self.tasks:
            task = self.tasks[task_id]
            tasks.append(task)
            for child_id in task.metadata.get("children", []):
                tasks.extend(self._collect_subtasks(child_id))
        return tasks


class TaskScheduler:
    """任务调度器，负责任务执行流程"""

    def __init__(self, task_manager: TaskManager, agent: "Agent"):
        self.task_manager = task_manager
        self.agent = agent
        self.execution_policy = "priority"  # 默认执行策略
        self.workers = []  # 工作线程
        self.task_queue = PriorityQueue()
        self.running_tasks = set()
        self.lock = threading.Lock()
        self.stop_event = threading.Event()

        # 启动调度线程
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop, daemon=True
        )
        self.scheduler_thread.start()

    def set_execution_policy(self, policy: str):
        """设置任务执行策略"""
        self.execution_policy = policy
        self.agent.log(f"Task execution policy set to: {policy}")

    def _scheduler_loop(self):
        """调度器主循环"""
        while not self.stop_event.is_set():
            # 检查就绪任务
            ready_tasks = self._find_ready_tasks()

            # 将就绪任务加入队列
            for task_id in ready_tasks:
                task = self.task_manager.get_task(task_id)
                tcb = self.task_manager.get_tcb(task_id)

                if not task or not tcb:
                    continue

                # 根据策略计算优先级
                if self.execution_policy == "priority":
                    priority = task.priority.value
                elif self.execution_policy == "fifo":
                    priority = tcb.metadata.get("created_at", time.time())
                else:  # default
                    priority = 0

                self.task_queue.put((priority, task_id))

            # 处理任务队列
            while not self.task_queue.empty() and not self.stop_event.is_set():
                # 修复解包错误：直接获取任务ID
                task_id = self.task_queue.get()
                tcb = self.task_manager.get_tcb(task_id)

                if not tcb:
                    continue

                if tcb.status == TaskStatus.READY:
                    # 标记为运行中
                    with self.lock:
                        tcb.status = TaskStatus.RUNNING
                        self.running_tasks.add(task_id)

                    # 在工作线程中执行任务
                    worker = threading.Thread(
                        target=self._execute_task, args=(task_id,), daemon=True
                    )
                    worker.start()
                    self.workers.append(worker)

            # 短暂休眠避免忙等待
            time.sleep(0.1)

    def _find_ready_tasks(self) -> List[str]:
        """查找所有就绪任务"""
        ready_tasks = []

        for task_id, tcb in self.task_manager.tcbs.items():
            if tcb.status == TaskStatus.CREATED and self._check_dependencies(task_id):
                tcb.status = TaskStatus.READY
                ready_tasks.append(task_id)

        return ready_tasks

    def _check_dependencies(self, task_id: str) -> bool:
        """检查任务依赖是否满足"""
        task = self.task_manager.get_task(task_id)
        if not task:
            return False

        for dep_id in task.dependencies:
            dep_tcb = self.task_manager.get_tcb(dep_id)
            if not dep_tcb or dep_tcb.status != TaskStatus.COMPLETED:
                return False

        return True

    def _execute_task(self, task_id: str):
        """执行单个任务"""
        task = self.task_manager.get_task(task_id)
        tcb = self.task_manager.get_tcb(task_id)

        if not task or not tcb:
            return

        try:
            # 记录开始时间
            tcb.start_time = time.time()
            tcb.log(f"Task execution started")

            # 模拟与LLM交互执行任务
            result = self._simulate_llm_interaction(task, tcb)

            # 更新任务状态
            tcb.result = result
            tcb.status = TaskStatus.COMPLETED
            tcb.end_time = time.time()
            tcb.progress = 1.0
            tcb.log(f"Task completed successfully. Result: {result[:50]}...")

            # 添加到agent记忆
            self.agent.memory.append(
                {
                    "task_id": task_id,
                    "prompt": task.prompt,
                    "result": result,
                    "execution_time": tcb.get_execution_time(),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        except Exception as e:
            # 任务失败处理
            tcb.status = TaskStatus.FAILED
            tcb.log(f"Task failed: {str(e)}")

        finally:
            # 清理运行状态
            with self.lock:
                if task_id in self.running_tasks:
                    self.running_tasks.remove(task_id)

    def _simulate_llm_interaction(self, task: Task, tcb: TCB) -> str:
        """模拟与LLM的交互过程"""
        # 模拟执行过程
        steps = 5  # 模拟多个步骤
        for step in range(steps):
            # 检查是否被取消
            if tcb.status == TaskStatus.CANCELED:
                tcb.log("Task canceled during execution")
                return "Canceled"

            # 更新进度
            progress = (step + 1) / steps
            tcb.update_progress(progress)

            # 模拟工作
            time.sleep(0.5)

            # 记录步骤
            tcb.log(f"Step {step+1}/{steps} completed")

        # 使用agent的上下文信息
        context = f"Agent knowledge: {self.agent.self_status['knowledge']}. Environment: {self.agent.env_status['location']}"

        # 模拟LLM响应
        return f"Processed task: '{task.prompt}'. Context: {context}. Used tools: {', '.join(task.tools)}"

    def get_task_queue_size(self) -> int:
        """获取任务队列大小"""
        return self.task_queue.qsize()

    def get_running_tasks(self) -> List[str]:
        """获取正在运行的任务ID"""
        with self.lock:
            return list(self.running_tasks)

    def cancel_task(self, task_id: str):
        """取消任务"""
        tcb = self.task_manager.get_tcb(task_id)
        if tcb:
            if tcb.status in [TaskStatus.READY, TaskStatus.PENDING]:
                tcb.status = TaskStatus.CANCELED
                tcb.log("Task canceled by user")
            elif tcb.status == TaskStatus.RUNNING:
                tcb.status = TaskStatus.CANCELED
                tcb.log("Task cancellation requested (running)")

    def retry_task(self, task_id: str):
        """重试任务"""
        tcb = self.task_manager.get_tcb(task_id)
        if tcb and tcb.status in [TaskStatus.FAILED, TaskStatus.CANCELED]:
            tcb.reset()
            tcb.log("Task scheduled for retry")

    def shutdown(self):
        """关闭调度器"""
        self.stop_event.set()
        self.scheduler_thread.join(timeout=1.0)


class PriorityQueue:
    """优先级队列实现"""

    def __init__(self):
        self.queue = []
        self.counter = 0  # 用于处理相同优先级

    def put(self, item: Tuple[float, Any]):
        """添加项目到队列"""
        priority, value = item
        heapq.heappush(self.queue, (-priority, self.counter, value))
        self.counter += 1

    def get(self) -> Any:
        """从队列获取项目"""
        if self.queue:
            _, _, value = heapq.heappop(self.queue)
            return value
        return None

    def empty(self) -> bool:
        """检查队列是否为空"""
        return len(self.queue) == 0

    def qsize(self) -> int:
        """获取队列大小"""
        return len(self.queue)


class Agent:
    """Agent主体类"""

    def __init__(self, name: str = "AI Agent"):
        self.name = name

        # 状态相关属性
        self.context: Dict[str, Any] = {"model": "gpt-4", "temperature": 0.7}
        self.self_status: Dict[str, Any] = {
            "knowledge": "general",
            "current_action": "idle",
            "current_task": None,
        }
        self.env_status: Dict[str, Any] = {
            "time": "day",
            "location": "unknown",
            "resources": {},
        }
        self.memory: List[Dict] = []
        self.default_tool = "default_search"

        # 任务管理系统
        self.task_manager = TaskManager()
        self.scheduler = TaskScheduler(self.task_manager, self)

    def log(self, message: str):
        """记录Agent日志"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [Agent] {message}"
        print_message(log_entry)
        self.memory.append(log_entry)

    def chat(self, message: str) -> str:
        """模拟与Agent的对话"""
        self.log(f"Received message: {message}")
        # 这里可以添加更多处理逻辑
        response = f"Agent response to '{message}'"
        self.log(f"Responding with: {response}")
        return response

    def run(self, prompt: str, tools: List[str] = None) -> str:
        """运行Agent"""
        task_id = self.create_task(prompt, tools)
        self.scheduler.set_execution_policy("priority")
        self.scheduler.run()
        return

    def create_task(
        self,
        prompt: str,
        tools: List[str] = None,
        resources: Dict[str, Any] = None,
        parent_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> Tuple[Task, TCB]:
        """创建新任务及其控制块"""
        if not tools:
            tools = [self.default_tool]
        return self.task_manager.create_task(
            prompt, tools, resources, parent_id, priority
        )

    def get_task_tree(self, task_id: str = None) -> Dict:
        """获取任务树结构"""
        return self.task_manager.get_task_tree(task_id)

    def get_task_dag(self, root_id: str = None) -> Dict[str, List[str]]:
        """获取任务DAG"""
        return self.task_manager.get_task_dag(root_id)

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态信息"""
        tcb = self.task_manager.get_tcb(task_id)
        if not tcb:
            return {}

        task = self.task_manager.get_task(task_id)
        return {
            "id": task_id,
            "prompt": task.prompt if task else "Unknown",
            "status": tcb.status.value,
            "progress": tcb.progress,
            "priority": task.priority.name if task else "Normal",
            "logs": tcb.logs[-5:],
            "execution_time": tcb.get_execution_time(),
            "dependencies": task.dependencies if task else [],
        }

    def cancel_task(self, task_id: str):
        """取消任务"""
        self.scheduler.cancel_task(task_id)

    def retry_task(self, task_id: str):
        """重试任务"""
        self.scheduler.retry_task(task_id)

    def get_scheduler_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            "policy": self.scheduler.execution_policy,
            "queue_size": self.scheduler.get_task_queue_size(),
            "running_tasks": self.scheduler.get_running_tasks(),
            "workers": len(self.scheduler.workers),
        }

    def shutdown(self):
        """关闭Agent系统"""
        self.scheduler.shutdown()


# 示例使用
if __name__ == "__main__":
    # 创建Agent
    agent = Agent("Research Assistant")

    # 设置Agent状态
    agent.self_status["knowledge"] = "AI research"
    agent.env_status["location"] = "research lab"
    agent.env_status["resources"] = {"datasets": ["Climate Data", "AI Publications"]}

    # 创建主任务
    main_task, main_tcb = agent.create_task(
        "Research the impact of AI on climate change",
        tools=["web_search", "data_analysis"],
        resources={"priority": "high"},
        priority=TaskPriority.HIGH,
    )

    # 创建子任务
    data_task, data_tcb = agent.create_task(
        "Gather climate data from reliable sources",
        parent_id=main_task.task_id,
        priority=TaskPriority.NORMAL,
    )

    analysis_task, analysis_tcb = agent.create_task(
        "Analyze AI energy consumption patterns",
        tools=["data_visualization"],
        parent_id=main_task.task_id,
        priority=TaskPriority.HIGH,
    )

    # 创建有依赖关系的任务
    report_task, report_tcb = agent.create_task(
        "Prepare final research report",
        parent_id=main_task.task_id,
        priority=TaskPriority.CRITICAL,
    )
    report_task.add_dependency(data_task.task_id)
    report_task.add_dependency(analysis_task.task_id)

    # 设置任务执行策略
    agent.scheduler.set_execution_policy("priority")

    # 查看任务树
    print_rule("Task Tree Structure:")
    print_json(agent.get_task_tree())

    # 查看任务DAG
    print("\nTask DAG:")
    print_json(agent.get_task_dag(main_task.task_id))

    # 查看调度器状态
    print("\nScheduler Status:")
    print_json(agent.get_scheduler_status())

    # 等待任务执行
    print_message("\nWaiting for tasks to complete...")
    try:
        while True:
            # 显示任务状态
            print_message("\nCurrent Task Status:")
            for task_id in agent.task_manager.tcbs:
                status = agent.get_task_status(task_id)
                print_message(
                    f"{task_id[:8]}: {status['status']} - {status['progress']:.0%} - {status['prompt'][:30]}..."
                )

            # 检查是否所有任务都已完成
            all_completed = all(
                tcb.status
                in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELED]
                for tcb in agent.task_manager.tcbs.values()
            )

            if all_completed:
                break

            time.sleep(2)
    except KeyboardInterrupt:
        print_message("\nInterrupted by user")

    # 查看最终任务状态
    print_message("\nFinal Task Status:")
    for task_id, tcb in agent.task_manager.tcbs.items():
        print_message(
            f"{task_id[:8]}: {tcb.status.name} - Result: {tcb.result[:50] if tcb.result else 'None'}"
        )

    # 查看最终任务树
    print_message("\nFinal Task Tree:")
    print_json(agent.get_task_tree())

    # 关闭系统
    agent.shutdown()
