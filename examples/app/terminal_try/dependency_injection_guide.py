"""
Remote Command 依赖注入获取外部实例详解
====================

本文档详细解释如何在 remote_command 工具中通过依赖注入获取 TaskManager、Executor 等外部实例。

## 核心概念

依赖注入（Dependency Injection）允许工具在运行时获取所需的外部实例，而不需要硬编码这些依赖关系。
这使得工具更加灵活、可测试，并且能够与不同的系统组件协作。

## 方案对比

### 方案一：ContextVar（推荐）✅
- **优点**: 异步安全、自动清理、支持嵌套调用
- **缺点**: 需要在任务执行前设置上下文
- **适用场景**: 异步环境、多任务并发场景

### 方案二：全局注册表
- **优点**: 简单直接、易于理解
- **缺点**: 需要手动管理生命周期、可能有线程安全问题
- **适用场景**: 简单应用、单线程环境

### 方案三：服务定位器
- **优点**: 企业级架构、支持复杂依赖管理
- **缺点**: 相对复杂、有隐式依赖
- **适用场景**: 大型应用、复杂系统架构

### 方案四：装饰器注入
- **优点**: 声明式、清晰的依赖关系
- **缺点**: 需要修改工具签名
- **适用场景**: 明确依赖关系的场景
"""

import asyncio
from contextvars import ContextVar
from typing import Optional, Any
from menglong.agents.component.tool_manager import tool


# =====================================
# 方案一：ContextVar 依赖注入（推荐）
# =====================================

# 定义上下文变量
task_manager_context: ContextVar[Optional[object]] = ContextVar(
    "task_manager", default=None
)
current_task_id_context: ContextVar[Optional[int]] = ContextVar(
    "current_task_id", default=None
)
remote_executor_context: ContextVar[Optional[object]] = ContextVar(
    "remote_executor", default=None
)


class DI:
    """简化的依赖注入管理器"""

    @staticmethod
    def set_context(task_manager, task_id: int, remote_executor=None):
        """设置依赖注入上下文"""
        task_manager_context.set(task_manager)
        current_task_id_context.set(task_id)
        if remote_executor:
            remote_executor_context.set(remote_executor)

    @staticmethod
    def get_task_manager():
        """获取 TaskManager 实例"""
        return task_manager_context.get()

    @staticmethod
    def get_task_id():
        """获取当前任务 ID"""
        return current_task_id_context.get()

    @staticmethod
    def get_executor():
        """获取远程执行器实例"""
        return remote_executor_context.get()


@tool
async def remote_command_v1(command: str, timeout: int = 30):
    """
    方案一：使用 ContextVar 的远程命令工具

    这是推荐的方案，因为：
    1. 异步安全 - 每个异步任务都有独立的上下文
    2. 自动清理 - 协程结束时自动清理上下文
    3. 嵌套安全 - 支持嵌套调用
    """
    # 获取注入的依赖
    task_manager = DI.get_task_manager()
    task_id = DI.get_task_id()
    executor = DI.get_executor()

    # 验证依赖是否可用
    if not task_manager:
        raise RuntimeError("❌ TaskManager 未通过依赖注入提供")

    if task_id is None:
        raise RuntimeError("❌ 当前任务 ID 未通过依赖注入提供")

    if not executor:
        print("⚠️  远程执行器不可用，降级为本地执行")
        return await _fallback_to_local(command)

    # 使用依赖执行远程命令
    try:
        request_id = await executor.send_command(task_id, command, timeout)

        print(f"✅ 远程命令已发送:")
        print(f"   请求 ID: {request_id}")
        print(f"   任务 ID: {task_id}")
        print(f"   命令: {command}")

        return {
            "status": "remote_pending",
            "request_id": request_id,
            "command": command,
            "task_id": task_id,
            "message": f"命令 '{command}' 已发送到远程服务器",
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "command": command,
            "task_id": task_id,
            "message": f"远程命令发送失败: {e}",
        }


# =====================================
# 方案二：全局注册表
# =====================================


class GlobalRegistry:
    """全局服务注册表"""

    _services = {}

    @classmethod
    def set(cls, key: str, value):
        cls._services[key] = value

    @classmethod
    def get(cls, key: str):
        return cls._services.get(key)


@tool
async def remote_command_v2(command: str, timeout: int = 30):
    """
    方案二：使用全局注册表的远程命令工具

    优点：简单直接
    缺点：需要手动管理生命周期，可能有并发问题
    """
    # 从全局注册表获取依赖
    task_manager = GlobalRegistry.get("task_manager")
    task_id = GlobalRegistry.get("task_id")
    executor = GlobalRegistry.get("executor")

    if not all([task_manager, task_id is not None, executor]):
        missing = []
        if not task_manager:
            missing.append("task_manager")
        if task_id is None:
            missing.append("task_id")
        if not executor:
            missing.append("executor")

        raise RuntimeError(f"❌ 缺少依赖: {', '.join(missing)}")

    # 执行远程命令逻辑...
    request_id = await executor.send_command(task_id, command, timeout)

    return {
        "status": "remote_pending",
        "request_id": request_id,
        "command": command,
        "injection_method": "global_registry",
    }


# =====================================
# 方案三：服务定位器（单例模式）
# =====================================


class ServiceLocator:
    """服务定位器单例"""

    _instance = None
    _services = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, service_type: str, instance):
        self._services[service_type] = instance

    def get(self, service_type: str):
        return self._services.get(service_type)

    def require(self, service_type: str):
        """获取服务，如果不存在则抛出异常"""
        service = self.get(service_type)
        if service is None:
            raise RuntimeError(f"❌ 必需的服务未注册: {service_type}")
        return service


@tool
async def remote_command_v3(command: str, timeout: int = 30):
    """
    方案三：使用服务定位器的远程命令工具

    优点：企业级架构，支持复杂依赖管理
    缺点：相对复杂，有隐式依赖
    """
    locator = ServiceLocator()

    try:
        # 获取必需的服务
        task_manager = locator.require("task_manager")
        task_id = locator.require("task_id")
        executor = locator.require("executor")

        request_id = await executor.send_command(task_id, command, timeout)

        return {
            "status": "remote_pending",
            "request_id": request_id,
            "command": command,
            "injection_method": "service_locator",
        }

    except RuntimeError as e:
        return {
            "status": "error",
            "error": str(e),
            "command": command,
            "injection_method": "service_locator",
        }


# =====================================
# 方案四：装饰器注入
# =====================================


def inject_dependencies(func):
    """依赖注入装饰器"""

    async def wrapper(*args, **kwargs):
        # 尝试从多个来源获取依赖
        task_manager = DI.get_task_manager() or GlobalRegistry.get("task_manager")
        task_id = DI.get_task_id() or GlobalRegistry.get("task_id")
        executor = DI.get_executor() or GlobalRegistry.get("executor")

        # 注入依赖到函数参数
        kwargs.update(
            {"_task_manager": task_manager, "_task_id": task_id, "_executor": executor}
        )

        return await func(*args, **kwargs)

    return wrapper


@tool
@inject_dependencies
async def remote_command_v4(
    command: str, timeout: int = 30, _task_manager=None, _task_id=None, _executor=None
):
    """
    方案四：使用装饰器注入的远程命令工具

    优点：声明式，清晰的依赖关系
    缺点：需要修改工具签名
    """
    if not all([_task_manager, _task_id is not None, _executor]):
        return {
            "status": "error",
            "error": "依赖注入失败",
            "command": command,
            "injection_method": "decorator",
        }

    request_id = await _executor.send_command(_task_id, command, timeout)

    return {
        "status": "remote_pending",
        "request_id": request_id,
        "command": command,
        "injection_method": "decorator",
    }


# =====================================
# 辅助函数
# =====================================


async def _fallback_to_local(command: str):
    """降级到本地执行"""
    import subprocess

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )

        return {
            "status": "local_executed",
            "command": command,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
            "message": "远程执行器不可用，已降级为本地执行",
        }

    except Exception as e:
        return {
            "status": "error",
            "command": command,
            "error": str(e),
            "message": f"本地执行也失败: {e}",
        }


# =====================================
# 集成示例
# =====================================


class TaskManagerWithDI:
    """支持依赖注入的 TaskManager 示例"""

    def __init__(self):
        self.remote_executor = None
        self.tasks = {}

    def set_remote_executor(self, executor):
        """设置远程执行器"""
        self.remote_executor = executor

    async def run_task_with_di(self, task_id: int):
        """带依赖注入的任务执行"""

        # 方案一：设置 ContextVar 上下文
        DI.set_context(
            task_manager=self, task_id=task_id, remote_executor=self.remote_executor
        )

        # 方案二：设置全局注册表
        GlobalRegistry.set("task_manager", self)
        GlobalRegistry.set("task_id", task_id)
        GlobalRegistry.set("executor", self.remote_executor)

        # 方案三：设置服务定位器
        locator = ServiceLocator()
        locator.register("task_manager", self)
        locator.register("task_id", task_id)
        locator.register("executor", self.remote_executor)

        print(f"✅ 依赖注入上下文已设置，任务 ID: {task_id}")

        # 现在可以调用任何需要依赖注入的工具
        # 例如：await remote_command_v1("ls -la")


# =====================================
# 使用示例
# =====================================


async def demo_all_injection_methods():
    """演示所有依赖注入方法"""

    print("🧪 依赖注入方案演示")
    print("=" * 50)

    # 创建模拟对象
    class MockExecutor:
        async def send_command(self, task_id, command, timeout):
            return f"mock_req_{task_id}_{hash(command) % 1000}"

    task_manager = TaskManagerWithDI()
    executor = MockExecutor()
    task_manager.set_remote_executor(executor)
    task_id = 123

    # 设置依赖注入上下文
    await task_manager.run_task_with_di(task_id)

    # 测试各种方案
    print("\n1️⃣ 测试 ContextVar 方案:")
    result1 = await remote_command_v1("echo 'test1'")
    print(f"   结果: {result1}")

    print("\n2️⃣ 测试全局注册表方案:")
    result2 = await remote_command_v2("echo 'test2'")
    print(f"   结果: {result2}")

    print("\n3️⃣ 测试服务定位器方案:")
    result3 = await remote_command_v3("echo 'test3'")
    print(f"   结果: {result3}")

    print("\n4️⃣ 测试装饰器注入方案:")
    result4 = await remote_command_v4("echo 'test4'")
    print(f"   结果: {result4}")

    print(f"\n🎉 所有依赖注入方案测试完成!")


if __name__ == "__main__":
    asyncio.run(demo_all_injection_methods())
