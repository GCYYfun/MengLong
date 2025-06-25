"""
TaskManager 依赖注入集成补丁
将依赖注入功能集成到现有的TaskManager中
"""

from contextvars import ContextVar
from typing import Optional

# 导入依赖注入组件
from remote_tool import DependencyInjector, GlobalServiceRegistry, ServiceLocator


class TaskManagerDependencyMixin:
    """TaskManager的依赖注入混入类"""

    def setup_dependency_injection(self, remote_executor=None):
        """设置依赖注入环境"""
        self.remote_executor = remote_executor

        # 注册到服务定位器
        locator = ServiceLocator()
        locator.register_service("task_manager", self)
        if remote_executor:
            locator.register_service("remote_executor", remote_executor)

    async def run_task_with_di(self, task_id: int):
        """运行任务时设置依赖注入上下文"""

        # 1. 设置ContextVar上下文（推荐方案）
        DependencyInjector.set_task_context(
            task_manager=self,
            task_id=task_id,
            remote_executor=getattr(self, "remote_executor", None),
        )

        # 2. 设置全局注册表
        GlobalServiceRegistry.register("task_manager", self)
        GlobalServiceRegistry.register("task_id", task_id)
        if hasattr(self, "remote_executor"):
            GlobalServiceRegistry.register("executor", self.remote_executor)

        # 3. 更新服务定位器
        locator = ServiceLocator()
        locator.register_service("current_task_id", task_id)

        try:
            # 调用原始的run_task方法
            return await self._original_run_task(task_id)
        finally:
            # 清理全局状态（ContextVar自动清理）
            GlobalServiceRegistry.register("task_id", None)


# 用于集成到现有TaskManager的代码片段
def patch_task_manager(task_manager_class):
    """为TaskManager类添加依赖注入功能"""

    # 保存原始的run_task方法
    original_run_task = task_manager_class.run_task

    async def run_task_with_injection(self, task_id: int):
        """带依赖注入的run_task方法"""

        # 设置依赖注入上下文
        DependencyInjector.set_task_context(
            task_manager=self,
            task_id=task_id,
            remote_executor=getattr(self, "remote_executor", None),
        )

        # 设置全局注册表
        GlobalServiceRegistry.register("task_manager", self)
        GlobalServiceRegistry.register("task_id", task_id)

        # 设置服务定位器
        locator = ServiceLocator()
        locator.register_service("task_manager", self)
        locator.register_service("current_task_id", task_id)
        if hasattr(self, "remote_executor"):
            locator.register_service("remote_executor", self.remote_executor)

        try:
            # 调用原始方法
            return await original_run_task(self, task_id)
        finally:
            # 清理全局状态
            GlobalServiceRegistry.register("task_id", None)

    # 替换run_task方法
    task_manager_class.run_task = run_task_with_injection

    # 添加remote_executor属性设置方法
    def set_remote_executor(self, executor):
        """设置远程执行器"""
        self.remote_executor = executor

        # 同时注册到服务定位器
        locator = ServiceLocator()
        locator.register_service("remote_executor", executor)

    task_manager_class.set_remote_executor = set_remote_executor

    return task_manager_class


# 使用示例
if __name__ == "__main__":
    # 假设你有一个TaskManager类
    # from task import TaskManager

    # 方法1: 直接应用补丁
    # TaskManager = patch_task_manager(TaskManager)

    # 方法2: 使用装饰器
    # @patch_task_manager
    # class MyTaskManager(TaskManager):
    #     pass

    print("TaskManager dependency injection patch ready!")
    print("使用方式:")
    print("1. task_manager.set_remote_executor(your_executor)")
    print("2. await task_manager.run_task(task_id)  # 自动注入依赖")
