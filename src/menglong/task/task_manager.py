import asyncio
from enum import Enum


class TaskState(Enum):
    """任务状态枚举

    描述任务在其生命周期内的各种状态
    """

    UNUSED = "UNUSED"  # 默认初始化，任务被创建但尚未加入调度队列
    READY = "READY"  # 准备就绪，不在运行，但随时可以被调度运行
    RUNNING = "RUNNING"  # 运行中，当前任务正在执行
    WAITING = "WAITING"  # 等待状态，当前任务暂停等待，所依赖的任务或子任务运行
    SUSPENDED = (
        "SUSPENDED"  # 挂起状态，任务尚未执行完毕，但被暂停，需要等待恢复后进入READY状态
    )
    CANCELED = "CANCELED"  # 已取消，任务被取消，不再进行执行
    COMPLETED = "COMPLETED"  # 已完成，任务顺利完成
    ERROR = "ERROR"  # 错误状态，任务出现未知情况，标记为错误状态
    DESTROYED = "DESTROYED"  # 销毁状态，任务已被销毁，资源已释放


class TCB:
    """任务控制块 (Task Control Block)

    存储任务的元数据和状态信息
    """

    def __init__(self, task_id, coroutine, loop=None):
        self.task_id = task_id  # 任务唯一标识符
        self.task = None  # asyncio.Task对象
        self.state = TaskState.UNUSED  # 初始状态为UNUSED
        self.coroutine = coroutine  # 协程对象
        self.created_time = (
            asyncio.get_running_loop().time() if loop is None else loop.time()
        )  # 创建时间
        self.start_time = None  # 开始执行时间
        self.complete_time = None  # 完成时间


class AsyncTaskScheduler:
    """异步任务调度器

    负责任务的创建、调度、暂停和恢复。主要功能包括：
    - 创建和销毁任务
    - 任务状态管理（挂起、恢复、等待、取消）
    - 任务状态查询
    - 调度器控制
    """

    def __init__(self):
        self.tasks = {}  # 任务字典，键为任务ID，值为TCB对象
        self.task_id_counter = 1  # 任务ID计数器
        self.loop = asyncio.new_event_loop()  # 事件循环
        self.current_task = None  # 当前正在执行的任务ID
        self.is_running = False  # 调度器是否正在运行

    def create_task(self, coroutine):
        """创建新任务

        Args:
            coroutine: 要执行的协程

        Returns:
            int: 任务ID
        """
        task_id = self.task_id_counter
        self.task_id_counter += 1

        async def wrapper():
            try:
                # 更新任务状态为RUNNING
                tcb = self.tasks[task_id]
                tcb.state = TaskState.RUNNING
                tcb.start_time = self.loop.time()
                self.current_task = task_id

                # 执行实际任务
                await coroutine

                # 任务完成，更新状态
                if task_id in self.tasks:  # 确保任务还存在
                    tcb = self.tasks[task_id]
                    tcb.state = TaskState.COMPLETED
                    tcb.complete_time = self.loop.time()
            except asyncio.CancelledError:
                # 任务被取消
                if task_id in self.tasks:
                    self.tasks[task_id].state = TaskState.CANCELED
            except Exception as e:
                # 任务发生错误
                if task_id in self.tasks:
                    self.tasks[task_id].state = TaskState.ERROR
                print(f"Task {task_id} error: {e}")
            finally:
                self.current_task = None
                # 不要立即销毁，让调度器可以查询最终状态
                # 可以通过定期清理已完成/取消的任务来优化内存

        # 创建TCB并初始化
        tcb = TCB(task_id, coroutine, self.loop)
        tcb.task = self.loop.create_task(wrapper())
        tcb.state = TaskState.READY  # 创建后立即设为就绪状态
        self.tasks[task_id] = tcb
        return task_id

    def destroy_task(self, task_id):
        """销毁任务，释放资源

        Args:
            task_id: 要销毁的任务ID
        """
        if task_id in self.tasks:
            tcb = self.tasks[task_id]
            if not tcb.task.done():
                tcb.task.cancel()
            tcb.state = TaskState.DESTROYED
            tcb.complete_time = self.loop.time()  # 记录销毁时间
            del self.tasks[task_id]

    def suspend_task(self, task_id):
        """挂起任务

        将任务置于挂起状态，暂停执行直到被恢复

        Args:
            task_id: 要挂起的任务ID
        """
        if task_id in self.tasks:
            tcb = self.tasks[task_id]
            if tcb.state in (TaskState.READY, TaskState.RUNNING):
                tcb.state = TaskState.SUSPENDED
                # 记录挂起行为
                print(f"Task {task_id} suspended at {self.loop.time()}")

    def resume_task(self, task_id):
        """恢复任务

        将挂起或等待的任务恢复到就绪状态

        Args:
            task_id: 要恢复的任务ID
        """
        if task_id in self.tasks:
            tcb = self.tasks[task_id]
            if tcb.state in (TaskState.SUSPENDED, TaskState.WAITING):
                tcb.state = TaskState.READY
                # 记录恢复行为
                print(f"Task {task_id} resumed at {self.loop.time()}")
                # 尝试调度任务
                self._try_schedule_task(tcb)

    def _try_schedule_task(self, tcb):
        """尝试调度任务

        内部方法，尝试将任务设为运行状态

        Args:
            tcb: 任务控制块
        """
        if tcb.state == TaskState.READY and self.current_task is None:
            tcb.state = TaskState.RUNNING
            self.current_task = tcb.task_id

    def cancel_task(self, task_id):
        """取消任务

        将任务标记为已取消，并停止执行

        Args:
            task_id: 要取消的任务ID

        Returns:
            bool: 取消是否成功
        """
        if task_id in self.tasks:
            tcb = self.tasks[task_id]
            if tcb.state not in (
                TaskState.COMPLETED,
                TaskState.CANCELED,
                TaskState.ERROR,
                TaskState.DESTROYED,
            ):
                tcb.state = TaskState.CANCELED
                tcb.task.cancel()
                tcb.complete_time = self.loop.time()  # 记录取消时间
                return True
        return False

    async def wait_task(self, task_id):
        """等待任务

        将当前任务设为等待状态，通常是等待另一个任务完成

        Args:
            task_id: 要等待的任务ID
        """
        if task_id in self.tasks:
            tcb = self.tasks[task_id]
            prev_state = tcb.state
            tcb.state = TaskState.WAITING
            # 记录状态变化
            print(f"Task {task_id} changed from {prev_state} to {TaskState.WAITING}")
            # 主动让出控制权
            await asyncio.sleep(0)

    def get_task_state(self, task_id):
        """获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            TaskState: 任务的当前状态
        """
        if task_id in self.tasks:
            return self.tasks[task_id].state
        return TaskState.DESTROYED  # 找不到任务，默认返回DESTROYED状态

    def get_task_info(self, task_id):
        """获取任务详细信息

        Args:
            task_id: 任务ID

        Returns:
            dict: 包含任务详细信息的字典，如果任务不存在则返回None
        """
        if task_id in self.tasks:
            tcb = self.tasks[task_id]
            current_time = self.loop.time()

            info = {
                "task_id": tcb.task_id,
                "state": tcb.state.value,
                "created_time": tcb.created_time,
                "start_time": tcb.start_time,
                "complete_time": tcb.complete_time,
                "elapsed_time": (current_time - (tcb.start_time or tcb.created_time)),
                "is_done": tcb.task.done() if tcb.task else False,
            }
            return info
        return None

    def run(self):
        """运行调度器的主循环

        阻塞调用，直到KeyboardInterrupt或调用stop()
        """
        self.is_running = True
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            print("Scheduler interrupted by keyboard")
        finally:
            self.is_running = False

            # 取消所有未完成的任务
            for task_id, tcb in list(self.tasks.items()):
                if tcb.task and not tcb.task.done():
                    tcb.task.cancel()

            # 清理剩余任务
            tasks_to_cancel = []
            for task in asyncio.all_tasks(self.loop):
                if not task.done():
                    task.cancel()
                    tasks_to_cancel.append(task)

            if tasks_to_cancel:
                try:
                    # 等待取消操作完成
                    self.loop.run_until_complete(
                        asyncio.wait(tasks_to_cancel, timeout=5)
                    )
                except Exception as e:
                    print(f"Error during cleanup: {e}")

            if not self.loop.is_closed():
                self.loop.close()

    def stop(self):
        """停止调度器

        优雅地停止调度器，取消所有任务
        """
        if self.is_running and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(self.loop.stop)


async def print_task_info(scheduler, task_id):
    """打印任务详细信息"""
    info = scheduler.get_task_info(task_id)
    if info:
        print(f"Task {task_id} Info:")
        print(f"  - State: {info['state']}")
        print(f"  - Created: {info['created_time']:.2f}s")
        print(
            f"  - Started: {info['start_time']:.2f}s"
            if info["start_time"]
            else "  - Started: Not started"
        )
        print(f"  - Elapsed: {info['elapsed_time']:.2f}s")
        print(f"  - Done: {info['is_done']}")
        print()


async def async_task1(scheduler):
    """演示任务1 - 展示等待状态和恢复机制"""
    print(f"Task 1 starting - RUNNING")
    await asyncio.sleep(1)  # 模拟IO操作

    print(f"Task 1 changing to WAITING state")
    await scheduler.wait_task(scheduler.current_task)

    print(f"Task 1 resumed from WAITING to RUNNING")
    await asyncio.sleep(0.5)
    print(f"Task 1 completing - will become COMPLETED")


async def async_task2(scheduler):
    """演示任务2 - 展示任务恢复和取消"""
    print(f"Task 2 starting - RUNNING")
    await asyncio.sleep(0.5)

    # 获取并打印任务1的状态
    task1_state = scheduler.get_task_state(1)
    print(f"Task 1 current state: {task1_state}")

    # 恢复任务1
    print(f"Resuming Task 1 from WAITING to READY")
    scheduler.resume_task(1)

    # 等待一下以便任务1可以运行
    await asyncio.sleep(0.1)
    print(f"Task 2 finishing - will become COMPLETED")


async def async_task3(scheduler):
    """演示任务3 - 展示挂起和取消"""
    print(f"Task 3 starting - RUNNING")

    for i in range(5):
        print(f"Task 3 working... step {i+1}/5")
        await asyncio.sleep(0.3)

        # 在第3步时检查是否需要挂起
        if i == 2:
            print(f"Task 3 will be suspended now")
            scheduler.suspend_task(3)
            # 挂起后，我们的代码仍会继续执行，但状态已经标记为SUSPENDED

    print(f"Task 3 finishing - showing completion despite suspension")


async def task_manager(scheduler):
    """元任务 - 管理其他任务的执行流程"""
    # 创建3个示例任务
    t1 = scheduler.create_task(async_task1(scheduler))
    t2 = scheduler.create_task(async_task2(scheduler))
    t3 = scheduler.create_task(async_task3(scheduler))

    print(f"Created 3 tasks with IDs: {t1}, {t2}, {t3}")

    # 让任务运行一段时间
    await asyncio.sleep(3)

    # 检查任务3状态，将其恢复
    task3_state = scheduler.get_task_state(3)
    print(f"\nTask 3 current state: {task3_state}")

    if task3_state == TaskState.SUSPENDED:
        print("Resuming suspended Task 3")
        scheduler.resume_task(3)

    # 等待任务继续执行
    await asyncio.sleep(1)

    # 取消任务3
    print("\nCancelling Task 3")
    scheduler.cancel_task(3)

    # 最终打印所有任务信息
    await asyncio.sleep(1)
    print("\n=== Final Task States ===")
    for task_id in [1, 2, 3]:
        await print_task_info(scheduler, task_id)

    # 停止调度器
    scheduler.stop()


if __name__ == "__main__":
    # 创建调度器
    scheduler = AsyncTaskScheduler()

    # 直接在调度器的事件循环中创建和运行任务管理器
    def start_tasks():
        # 启动任务管理器
        main_task = scheduler.create_task(task_manager(scheduler))
        print(f"Created main task with ID: {main_task}")

    # 将任务启动函数安排到事件循环中运行
    scheduler.loop.call_soon(start_tasks)

    print("Scheduler starting...")
    try:
        scheduler.run()
    except Exception as e:
        print(f"Scheduler error: {e}")
    finally:
        print("Scheduler stopped.")
