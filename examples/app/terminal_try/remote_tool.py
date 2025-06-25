"""
远程工具执行示例
演示如何集成WebSocket远程执行与任务系统
"""

import asyncio
import json
from menglong.agents.component.tool_manager import tool


@tool
def remote_command(command: str, timeout: int = 30):
    """
    发送命令到远程服务器执行

    参数:
        command (str): 要在远程执行的命令
        timeout (int): 超时时间（秒）

    返回:
        dict: 包含请求ID和状态的字典
    """
    # 这个工具会被任务系统调用
    # 它需要能够访问任务管理器来挂起任务

    # 注意：这里需要通过某种方式获取当前的task_manager实例
    # 在实际使用时，可以通过全局变量、依赖注入等方式实现

    return {
        "status": "remote_pending",
        "command": command,
        "timeout": timeout,
        "message": f"Command '{command}' sent to remote server, waiting for response...",
    }


class WebSocketRemoteExecutor:
    """
    WebSocket远程执行器示例
    这个类处理与远程服务器的WebSocket通信
    """

    def __init__(self, task_manager):
        self.task_manager = task_manager
        self.websocket = None

    async def connect(self, ws_url: str):
        """连接到WebSocket服务器"""
        # 这里应该是实际的WebSocket连接代码
        print(f"Connecting to WebSocket: {ws_url}")
        pass

    async def send_command(self, task_id: int, command: str, timeout: int = 30) -> str:
        """
        发送命令到远程服务器并挂起任务

        返回请求ID
        """
        # 1. 挂起任务
        request_id = await self.task_manager.suspend_task_for_remote(
            task_id, command, timeout
        )

        # 2. 发送命令到远程服务器（通过WebSocket）
        message = {"request_id": request_id, "command": command, "task_id": task_id}

        # 这里应该是实际的WebSocket发送代码
        print(f"Sending to remote: {json.dumps(message)}")
        # await self.websocket.send(json.dumps(message))

        return request_id

    async def handle_websocket_message(self, message: str):
        """
        处理从WebSocket接收的消息
        这个方法应该在WebSocket的事件监听器中调用
        """
        try:
            data = json.loads(message)
            request_id = data.get("request_id")
            success = data.get("success", False)
            result = data.get("result")
            error = data.get("error")

            if request_id:
                # 调用任务管理器处理响应
                self.task_manager.handle_websocket_response(
                    request_id, success, result, error
                )

        except Exception as e:
            print(f"Error handling WebSocket message: {e}")


# 使用示例
async def example_usage():
    """使用示例"""

    # 假设你有一个任务管理器实例
    # task_manager = TaskManager(agent)

    # 创建WebSocket执行器
    # executor = WebSocketRemoteExecutor(task_manager)

    # 连接到远程服务器
    # await executor.connect("ws://remote-server:8080/execute")

    # 在任务中使用远程执行
    # request_id = await executor.send_command(task_id=1, command="ls -la")

    # 当WebSocket接收到响应时，调用处理器
    # 例如，在WebSocket事件监听器中：
    # websocket.on_message = executor.handle_websocket_message

    print("Remote execution system ready!")


if __name__ == "__main__":
    asyncio.run(example_usage())
