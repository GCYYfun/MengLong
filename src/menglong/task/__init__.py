"""
任务管理器模块导引

本文档提供了对任务管理器模块的简要概览和使用指南。
"""

# 导入任务管理器类和任务状态枚举
from src.menglong.task.task_manager import AsyncTaskScheduler, TaskState

# 使用示例
if __name__ == "__main__":
    # 提示用户
    print("这是任务管理器模块的导引文件，不是直接运行的脚本。")
    print("请查看以下文件了解如何使用任务管理器：")
    print("- src/menglong/task/README.md - 详细文档")
    print("- examples/demo/task_manager_demo.py - 演示示例")
    print("\n基本用法示例:")

    # 基本用法示例代码
    code_example = """
    import asyncio
    from src.menglong.task.task_manager import AsyncTaskScheduler, TaskState
    
    async def my_task():
        print("任务开始")
        await asyncio.sleep(1)
        print("任务完成")
    
    # 创建调度器
    scheduler = AsyncTaskScheduler()
    
    # 创建一个管理函数
    async def run_tasks():
        # 创建任务
        task_id = scheduler.create_task(my_task())
        
        # 等待任务完成
        await asyncio.sleep(2)
        
        # 停止调度器
        scheduler.stop()
    
    # 将管理函数添加到调度器
    scheduler.loop.call_soon(lambda: scheduler.create_task(run_tasks()))
    
    # 运行调度器
    scheduler.run()
    """

    print(code_example)
