"""
完整的依赖注入与远程工具集成示例
演示如何让工具获取 TaskManager、Executor 等外部实例
"""

import asyncio
import json
from contextvars import ContextVar
from typing import Optional, Any, Dict
from menglong.agents.component.tool_manager import tool
from remote_tool import DependencyInjector, WebSocketRemoteExecutor
from task import TaskManager


class EnhancedTaskManager(TaskManager):
    """增强的TaskManager，支持依赖注入"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.remote_executor = None
        self.injection_enabled = True

    def set_remote_executor(self, executor):
        """设置远程执行器"""
        self.remote_executor = executor
        print(f"✓ RemoteExecutor 已设置: {executor}")

    async def run_task(self, task_id: int) -> Any:
        """重写 run_task，在执行前设置依赖注入上下文"""

        if self.injection_enabled:
            # 设置依赖注入上下文
            self._setup_dependency_injection(task_id)

        try:
            # 调用父类的 run_task 方法
            result = await super().run_task(task_id)
            return result
        finally:
            # 清理上下文（如果需要）
            if self.injection_enabled:
                self._cleanup_dependency_injection()

    def _setup_dependency_injection(self, task_id: int):
        """设置依赖注入上下文"""
        print(f"🔧 Setting up dependency injection for task {task_id}")

        # 1. 设置 ContextVar（推荐方案）
        DependencyInjector.set_task_context(
            task_manager=self, task_id=task_id, remote_executor=self.remote_executor
        )

        # 2. 设置全局注册表（备用方案）
        from remote_tool import GlobalServiceRegistry

        GlobalServiceRegistry.register("task_manager", self)
        GlobalServiceRegistry.register("task_id", task_id)
        if self.remote_executor:
            GlobalServiceRegistry.register("executor", self.remote_executor)

        # 3. 设置服务定位器（企业级方案）
        from remote_tool import ServiceLocator

        locator = ServiceLocator()
        locator.register_service("task_manager", self)
        locator.register_service("current_task_id", task_id)
        if self.remote_executor:
            locator.register_service("remote_executor", self.remote_executor)

        print(f"✓ Dependency injection context set for task {task_id}")

    def _cleanup_dependency_injection(self):
        """清理依赖注入上下文"""
        # ContextVar 会自动清理，但我们可以清理全局状态
        from remote_tool import GlobalServiceRegistry

        GlobalServiceRegistry.register("task_id", None)
        print("✓ Dependency injection context cleaned up")


# 示例：创建能获取外部实例的工具
@tool
async def enhanced_terminal_command(command: str):
    """
    增强的终端命令工具，能够获取 TaskManager 和当前任务ID
    """
    # 通过依赖注入获取外部实例
    task_manager = DependencyInjector.get_task_manager()
    current_task_id = DependencyInjector.get_current_task_id()

    print(f"🔍 Tool accessing TaskManager: {task_manager}")
    print(f"🔍 Current task ID: {current_task_id}")

    if task_manager:
        # 获取当前任务的详细信息
        task = task_manager.get_task(current_task_id)
        task_desc = task_manager.get_task_desc(current_task_id)
        print(f"📋 Current task prompt: {task.prompt if task else 'Unknown'}")
        print(f"📊 Task status: {task_desc.status if task_desc else 'Unknown'}")

    # 执行实际的终端命令
    import subprocess

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )

        execution_info = {
            "command": command,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
            "task_id": current_task_id,
            "executed_by": "enhanced_terminal_command",
        }

        print(f"✓ Command executed: {command}")
        print(f"✓ Exit code: {result.returncode}")

        return execution_info

    except subprocess.TimeoutExpired:
        return {
            "command": command,
            "exit_code": -1,
            "stdout": "",
            "stderr": "Command timed out",
            "success": False,
            "task_id": current_task_id,
            "executed_by": "enhanced_terminal_command",
        }
    except Exception as e:
        return {
            "command": command,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False,
            "task_id": current_task_id,
            "executed_by": "enhanced_terminal_command",
        }


@tool
async def get_task_manager_status():
    """
    获取 TaskManager 状态信息的工具
    """
    task_manager = DependencyInjector.get_task_manager()
    current_task_id = DependencyInjector.get_current_task_id()

    if not task_manager:
        return {"error": "TaskManager not available through dependency injection"}

    # 收集任务管理器状态信息
    status_info = {
        "current_task_id": current_task_id,
        "total_tasks": len(task_manager.tasks),
        "pending_tasks": len(
            [
                tid
                for tid, task_desc in task_manager.task_descriptions.items()
                if task_desc.status.value == "PENDING"
            ]
        ),
        "running_tasks": len(
            [
                tid
                for tid, task_desc in task_manager.task_descriptions.items()
                if task_desc.status.value == "RUNNING"
            ]
        ),
        "completed_tasks": len(
            [
                tid
                for tid, task_desc in task_manager.task_descriptions.items()
                if task_desc.status.value == "COMPLETED"
            ]
        ),
        "scheduler_running": getattr(task_manager, "scheduler_running", False),
        "remote_executor_available": hasattr(task_manager, "remote_executor")
        and task_manager.remote_executor is not None,
    }

    print(f"📊 TaskManager Status: {status_info}")
    return status_info


@tool
async def remote_command_with_injection(command: str, timeout: int = 30):
    """
    使用依赖注入的远程命令工具
    """
    # 获取注入的依赖
    task_manager = DependencyInjector.get_task_manager()
    current_task_id = DependencyInjector.get_current_task_id()
    remote_executor = DependencyInjector.get_remote_executor()

    print(f"🌐 Remote command tool called:")
    print(f"  - TaskManager: {'✓' if task_manager else '✗'}")
    print(f"  - Task ID: {current_task_id}")
    print(f"  - Remote Executor: {'✓' if remote_executor else '✗'}")

    if not task_manager:
        return {"error": "TaskManager not found in context"}

    if current_task_id is None:
        return {"error": "Current task ID not found in context"}

    if not remote_executor:
        # 如果没有远程执行器，提供降级处理
        print("⚠️  No remote executor available, falling back to local execution")
        return await enhanced_terminal_command(command)

    try:
        # 发送远程命令
        request_id = await remote_executor.send_command(
            current_task_id, command, timeout
        )

        return {
            "status": "remote_pending",
            "request_id": request_id,
            "command": command,
            "timeout": timeout,
            "task_id": current_task_id,
            "message": f"Command '{command}' sent to remote server, request ID: {request_id}",
        }
    except Exception as e:
        return {
            "status": "error",
            "command": command,
            "task_id": current_task_id,
            "error": str(e),
            "message": f"Failed to send command '{command}' to remote server: {e}",
        }


class MockWebSocketRemoteExecutor(WebSocketRemoteExecutor):
    """模拟的 WebSocket 远程执行器"""

    def __init__(self, task_manager):
        super().__init__(task_manager)
        self.request_counter = 0

    async def send_command(self, task_id: int, command: str, timeout: int = 30) -> str:
        """模拟发送命令到远程服务器"""
        self.request_counter += 1
        request_id = f"mock_req_{self.request_counter}_{task_id}"

        print(f"🌐 Mock sending command to remote server:")
        print(f"  - Request ID: {request_id}")
        print(f"  - Task ID: {task_id}")
        print(f"  - Command: {command}")
        print(f"  - Timeout: {timeout}s")

        # 模拟挂起任务
        await self.task_manager.suspend_task_for_remote(task_id, command, timeout)

        # 模拟异步响应（在实际应用中，这会通过WebSocket异步返回）
        asyncio.create_task(self._simulate_remote_response(request_id, command))

        return request_id

    async def _simulate_remote_response(self, request_id: str, command: str):
        """模拟远程服务器响应"""
        # 等待一段时间模拟网络延迟
        await asyncio.sleep(2.0)

        # 模拟命令执行结果
        if "error" in command.lower():
            # 模拟错误情况
            self.task_manager.handle_websocket_response(
                request_id=request_id,
                success=False,
                result=None,
                error=f"Remote execution failed for: {command}",
            )
        else:
            # 模拟成功情况
            mock_result = {
                "command": command,
                "exit_code": 0,
                "stdout": f"Mock output for: {command}",
                "stderr": "",
                "success": True,
                "executed_remotely": True,
                "request_id": request_id,
            }
            self.task_manager.handle_websocket_response(
                request_id=request_id, success=True, result=mock_result, error=None
            )

        print(f"🌐 Mock remote response sent for request: {request_id}")


async def demo_complete_integration():
    """完整集成示例"""
    print("=" * 60)
    print("🚀 完整的依赖注入与远程工具集成示例")
    print("=" * 60)

    # 1. 创建增强的 TaskManager
    enhanced_manager = EnhancedTaskManager()

    # 2. 创建模拟的远程执行器
    mock_executor = MockWebSocketRemoteExecutor(enhanced_manager)
    enhanced_manager.set_remote_executor(mock_executor)

    # 3. 创建测试任务
    from task import TaskDetail, TaskDescription, TaskStatus
    from task_agent import ChatAgent

    # 创建一个使用依赖注入工具的任务
    test_tools = [
        enhanced_terminal_command,
        get_task_manager_status,
        remote_command_with_injection,
    ]

    task = TaskDetail(
        prompt="测试依赖注入功能：检查系统状态并执行一些命令",
        tools=test_tools,
        result=None,
    )

    # 添加任务到管理器
    task_id = enhanced_manager.add_task(task, [], context=ChatAgent())

    print(f"\n📋 创建测试任务 ID: {task_id}")
    print(f"🔧 工具列表: {[tool._tool_info.name for tool in test_tools]}")

    # 4. 执行任务（这会自动设置依赖注入上下文）
    print(f"\n🏃 开始执行任务...")
    try:
        result = await enhanced_manager.run_task(task_id)
        print(f"\n✅ 任务执行完成")
        print(f"📊 执行结果: {result}")
    except Exception as e:
        print(f"\n❌ 任务执行失败: {e}")

    # 5. 测试直接调用工具（需要手动设置上下文）
    print(f"\n🧪 测试直接调用工具...")

    # 手动设置依赖注入上下文
    DependencyInjector.set_task_context(
        task_manager=enhanced_manager, task_id=task_id, remote_executor=mock_executor
    )

    # 测试获取任务管理器状态
    status = await get_task_manager_status()
    print(f"📊 TaskManager 状态: {status}")

    # 测试增强的终端命令
    local_result = await enhanced_terminal_command("echo 'Hello from local command'")
    print(f"💻 本地命令结果: {local_result}")

    # 测试远程命令
    remote_result = await remote_command_with_injection(
        "echo 'Hello from remote command'"
    )
    print(f"🌐 远程命令结果: {remote_result}")

    # 等待远程响应
    print(f"\n⏳ 等待远程响应...")
    await asyncio.sleep(3)

    print(f"\n🎉 集成示例演示完成!")


if __name__ == "__main__":
    asyncio.run(demo_complete_integration())
