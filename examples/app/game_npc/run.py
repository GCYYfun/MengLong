import trio
from npc_agent import NpcAgent


async def main():
    print("Game NPC is running...")
    agent = NpcAgent(name="Game NPC")
    await agent.run()
    print("Game NPC has finished running.")


if __name__ == "__main__":
    trio.run(main)
