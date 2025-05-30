"""
任务管理器示例演示

本脚本展示了如何使用AsyncTaskScheduler来管理异步任务和其状态。
演示了任务创建、监控、等待、挂起、恢复和取消等功能。
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加项目根目录到系统路径以便导入
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.menglong.task.task_manager import AsyncTaskScheduler, TaskState


async def print_task_info(scheduler, task_id):
    """打印任务详细信息"""
    info = scheduler.get_task_info(task_id)
    if info:
        print(f"\n🔍 任务 {task_id} 信息:")
        print(f"  - 状态: {info['state']}")
        print(f"  - 创建: {info['created_time']:.2f}s")
        if info["start_time"]:
            print(f"  - 启动: {info['start_time']:.2f}s")
        print(f"  - 运行时间: {info['elapsed_time']:.2f}s")
        print(f"  - 是否完成: {info['is_done']}")


async def task_with_steps(scheduler, name, steps=5, step_time=0.5):
    """模拟一个分步骤执行的任务"""
    print(f"\n▶️ {name} 开始执行 (任务ID: {scheduler.current_task})")

    for i in range(steps):
        print(f"  📍 {name} 步骤 {i+1}/{steps}")
        await asyncio.sleep(step_time)

        # 在中间步骤打印当前状态
        if i == steps // 2:
            state = scheduler.get_task_state(scheduler.current_task)
            print(f"  ℹ️ {name} 当前状态: {state}")

    print(f"✅ {name} 完成执行")


async def waiting_task(scheduler, wait_time=2):
    """演示等待状态的任务"""
    task_id = scheduler.current_task
    print(f"\n⏱️ 等待任务 {task_id} 启动")

    await asyncio.sleep(1)
    print(f"⏸️ 任务 {task_id} 进入等待状态")

    # 将自身设置为等待状态
    await scheduler.wait_task(task_id)

    print(f"▶️ 任务 {task_id} 已恢复，完成剩余工作")
    await asyncio.sleep(wait_time)
    print(f"✅ 等待任务 {task_id} 完成")


async def control_task(scheduler, tasks_to_manage):
    """控制其他任务的任务"""
    print(f"\n🎮 控制任务开始")
    await asyncio.sleep(3)  # 先让其他任务运行一会

    # 演示挂起操作
    suspend_task = tasks_to_manage[0]
    print(f"⏸️ 挂起任务 {suspend_task}")
    scheduler.suspend_task(suspend_task)

    await asyncio.sleep(2)  # 等待一段时间

    # 演示恢复操作
    print(f"▶️ 恢复任务 {suspend_task}")
    scheduler.resume_task(suspend_task)

    await asyncio.sleep(1)  # 等待一段时间

    # 恢复等待状态的任务
    waiting_task_id = tasks_to_manage[1]
    print(f"▶️ 恢复等待任务 {waiting_task_id}")
    scheduler.resume_task(waiting_task_id)

    # 取消某个任务
    if len(tasks_to_manage) > 2:
        cancel_task = tasks_to_manage[2]
        await asyncio.sleep(0.5)
        print(f"❌ 取消任务 {cancel_task}")
        scheduler.cancel_task(cancel_task)

    # 等待其他任务完成
    await asyncio.sleep(5)
    print("🎮 控制任务完成")


async def monitor_tasks(scheduler, task_ids):
    """监控多个任务的状态"""
    print("\n📊 任务监控启动")

    # 持续监控，直到所有任务完成
    while any(
        scheduler.get_task_state(tid)
        not in (
            TaskState.COMPLETED,
            TaskState.CANCELED,
            TaskState.ERROR,
            TaskState.DESTROYED,
        )
        for tid in task_ids
    ):

        print("\n当前任务状态:")
        for task_id in task_ids:
            state = scheduler.get_task_state(task_id)
            print(f"  - 任务 {task_id}: {state}")

        await asyncio.sleep(1)

    print("📊 所有任务已完成，监控结束")


async def task_orchestrator(scheduler):
    """任务编排器，负责创建和协调所有任务"""
    print("🚀 任务编排器启动")
    tasks = []

    # 创建正常任务
    task1 = scheduler.create_task(
        task_with_steps(scheduler, "普通任务", steps=8, step_time=0.6)
    )
    tasks.append(task1)

    # 创建等待任务
    task2 = scheduler.create_task(waiting_task(scheduler, wait_time=2))
    tasks.append(task2)

    # 创建将被取消的任务
    task3 = scheduler.create_task(
        task_with_steps(scheduler, "可能被取消的任务", steps=15, step_time=0.4)
    )
    tasks.append(task3)

    # 创建控制任务
    control = scheduler.create_task(control_task(scheduler, tasks))

    # 创建监控任务
    monitor = scheduler.create_task(monitor_tasks(scheduler, tasks))

    # 等待足够长的时间让所有任务完成
    await asyncio.sleep(12)

    # 打印最终状态
    print("\n====== 最终任务状态 ======")
    for task_id in tasks:
        await print_task_info(scheduler, task_id)

    print("\n🏁 任务编排结束，关闭调度器")
    scheduler.stop()


def main():
    """主函数"""
    print("====== 异步任务管理器演示 ======")

    # 创建调度器
    scheduler = AsyncTaskScheduler()

    # 安排任务编排器
    def start():
        scheduler.create_task(task_orchestrator(scheduler))

    scheduler.loop.call_soon(start)

    try:
        print("调度器启动中...")
        start_time = time.time()
        scheduler.run()
        elapsed = time.time() - start_time
        print(f"\n调度器已停止，运行时间: {elapsed:.2f}秒")
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"\n错误: {e}")


if __name__ == "__main__":
    main()
