from abc import ABC, abstractmethod
from ..ml_model import Model


class Agent(ABC):
    def __init__(
        self,
        model_id: str = None,
    ):
        # model
        if model_id is None:
            self.model = Model()
        else:
            self.model = Model(model_id=model_id)

    @abstractmethod
    def run(self):
        """执行代理任务"""
        pass

    @abstractmethod
    async def stop(self):
        """停止代理任务"""
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """检查代理是否正在运行"""
        pass
