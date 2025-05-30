from menglong.agents.agent import Agent


class NpcAgent(Agent):
    """
    NPC代理类
    该类用于创建一个NPC代理，继承自Agent类。
    """

    def __init__(self, name):
        self.name = name

    async def run(self):
        print(f"NPC {self.name} is running...")
