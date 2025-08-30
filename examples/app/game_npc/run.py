import asyncio
import json
from pathlib import Path
import sys
from datetime import datetime


from game_world import GameWorld, create_demo_world
from npc_agent import NPCAgent, NPCPersonality, EmotionType
from npc_factory import NPCFactory, create_configured_world, analyze_npc


async def demo_single_npc():
    """演示单个NPC的运行"""
    print("=== 单个NPC演示 ===")

    # 创建一个具有特定个性的NPC
    personality = NPCPersonality(
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.9,
        agreeableness=0.8,
        neuroticism=0.3,
        creativity=0.9,
        ambition=0.7,
        empathy=0.8,
        curiosity=0.8,
    )

    npc = NPCAgent("艾莉丝", personality=personality)

    # 设置世界信息
    npc.set_world_info(
        locations=["home", "work", "park", "library", "market"],
        npcs=["朋友A", "朋友B", "邻居C"],
        events=["音乐节", "集市"],
    )

    # 添加一些初始目标
    from npc_agent import Goal

    npc.goals.extend(
        [
            Goal(description="学习新技能", priority=0.8, progress=0.0, completed=False),
            Goal(description="建立友谊", priority=0.6, progress=0.2, completed=False),
        ]
    )

    print(f"NPC {npc.name} 创建完成")
    print(f"个性特征: {npc.personality}")

    # 设置世界信息
    npc.set_world_info(
        locations=["home", "park", "cafe", "library", "market", "gym"],
        npcs=["小明", "小红", "老李", "张三", "李四"],
        events=["音乐会", "市场开业", "读书会"],
    )

    # 分析NPC
    analysis = analyze_npc(npc)
    print(f"\n个性分析: {analysis['personality_analysis']}")
    print(f"行为预测: {analysis['behavior_prediction']}")

    print(f"\n初始状态: {npc.get_status_report()}")

    # 运行NPC一段时间
    print("\n开始运行NPC...")
    print("观察NPC的自主决策和行为...")

    # 设置较短的决策间隔用于演示
    npc.decision_interval = 5  # 5秒做一次决策

    # 运行60秒
    try:
        await asyncio.wait_for(npc.run(), timeout=60)
    except asyncio.TimeoutError:
        npc.stop_autonomous_life()
        print("演示结束")

    # 显示最终状态
    print(f"\n最终状态报告:")
    final_report = npc.get_status_report()
    print(json.dumps(final_report, indent=2, ensure_ascii=False))


async def demo_world_simulation():
    """演示完整的世界模拟"""
    print("=== 游戏世界模拟演示 ===")

    # 创建演示世界
    world = create_demo_world()

    # 显示世界初始状态
    print("世界初始状态:")
    initial_report = world.generate_world_report()
    print(f"- 位置数量: {len(world.locations)}")
    print(f"- NPC数量: {initial_report['npc_count']}")
    print(f"- 天气: {initial_report['weather']}")
    print(f"- 当前时间: {initial_report['current_time']}")

    print("\nNPC个性概览:")
    for name, npc in world.npcs.items():
        analysis = analyze_npc(npc)
        print(f"{name}: {analysis['personality_analysis']['extraversion']}")

    # 为演示设置更快的时间流逝
    for npc in world.npcs.values():
        npc.decision_interval = 15  # 15秒做一次决策

    print("\n开始世界模拟...")
    print("观察NPC之间的互动和世界事件...")
    print("(按 Ctrl+C 停止)")

    try:
        await asyncio.wait_for(world.start_world(), timeout=120)  # 运行2分钟
    except asyncio.TimeoutError:
        print("演示时间结束")
    except KeyboardInterrupt:
        print("\n用户中断")
    finally:
        world.stop_world()

        # 显示最终世界状态
        print("\n=== 最终世界状态 ===")
        final_report = world.generate_world_report()

        print(f"模拟时间: {final_report['current_time']}")
        print(f"天气: {final_report['weather']}")
        print(f"活跃事件: {final_report['active_events']}")

        print("\nNPC状态总结:")
        for name, npc_data in final_report["npcs"].items():
            print(f"\n{name}:")
            print(f"  - 位置: {npc_data['status']['location']}")
            print(f"  - 活动: {npc_data['status']['activity']}")
            print(f"  - 情绪: {npc_data['status']['current_emotion']}")
            print(f"  - 幸福感: {npc_data['status']['happiness']:.1f}%")
            print(f"  - 能量: {npc_data['status']['energy']:.1f}%")
            print(f"  - 关系数量: {len(npc_data['relationships'])}")
            print(f"  - 目标数量: {len(npc_data['goals'])}")

            if npc_data["recent_memories"]:
                print(f"  - 最近记忆: {npc_data['recent_memories'][-1]['content']}")


async def demo_configured_world():
    """演示配置文件驱动的世界"""
    print("=== 配置文件驱动的世界演示 ===")

    try:
        # 从配置文件创建世界
        world = create_configured_world("config.yaml")

        # 显示配置信息
        factory = NPCFactory("config.yaml")
        presets = factory.get_available_presets()
        print(f"可用个性预设: {presets}")

        # 显示世界信息
        print(f"\n世界信息:")
        print(f"- 位置: {world.locations}")
        print(f"- 可能的事件: {[e.name for e in world.possible_events]}")

        # 显示NPC信息
        print(f"\nNPC信息:")
        for name, npc in world.npcs.items():
            analysis = analyze_npc(npc)
            print(f"{name}:")
            print(f"  - 个性: {analysis['personality_analysis']['extraversion']}")
            print(f"  - 预测行为: {analysis['behavior_prediction']['social']}")

        # 快速模拟
        for npc in world.npcs.values():
            npc.decision_interval = 20

        print("\n开始配置世界模拟...")
        await asyncio.wait_for(world.start_world(), timeout=60)

    except Exception as e:
        print(f"配置世界演示失败: {e}")
        print("使用默认演示...")
        await demo_world_simulation()


async def interactive_demo():
    """交互式演示"""
    print("=== 交互式NPC演示 ===")

    # 创建世界
    world = create_demo_world()

    print("可用命令:")
    print("  status - 显示世界状态")
    print("  npc <name> - 显示特定NPC详情")
    print("  analyze <name> - 分析特定NPC")
    print("  event - 触发随机事件")
    print("  time - 推进时间")
    print("  start - 开始自动模拟")
    print("  stop - 停止自动模拟")
    print("  list - 列出所有NPC")
    print("  help - 显示帮助")
    print("  quit - 退出")

    running = True
    auto_simulation = False
    simulation_task = None

    while running:
        try:
            command = input("\n> ").strip().lower()

            if command == "quit":
                running = False
                if simulation_task:
                    world.stop_world()
                    simulation_task.cancel()

            elif command == "status":
                report = world.generate_world_report()
                print(f"时间: {report['current_time']}")
                print(f"天气: {report['weather']}")
                print(f"活跃事件: {report['active_events']}")
                print(f"NPC列表: {list(report['npcs'].keys())}")

            elif command.startswith("npc "):
                npc_name = command[4:].strip()
                if npc_name in world.npcs:
                    npc_data = world.npcs[npc_name].get_status_report()
                    print(json.dumps(npc_data, indent=2, ensure_ascii=False))
                else:
                    print(f"NPC '{npc_name}' 不存在")

            elif command.startswith("analyze "):
                npc_name = command[8:].strip()
                if npc_name in world.npcs:
                    analysis = analyze_npc(world.npcs[npc_name])
                    print(f"{npc_name} 的分析:")
                    print(f"个性分析: {analysis['personality_analysis']}")
                    print(f"行为预测: {analysis['behavior_prediction']}")
                    print(f"关系分析: {analysis['relationship_analysis']}")
                else:
                    print(f"NPC '{npc_name}' 不存在")

            elif command == "event":
                world.trigger_random_event()

            elif command == "time":
                world.update_time()
                print(f"时间推进到: {world.current_time}")

            elif command == "list":
                print("NPC列表:")
                for name, npc in world.npcs.items():
                    print(
                        f"  {name}: {npc.current_location} - {npc.status.current_emotion.value}"
                    )

            elif command == "start":
                if not auto_simulation:
                    auto_simulation = True
                    # 设置快速决策间隔
                    for npc in world.npcs.values():
                        npc.decision_interval = 20
                    simulation_task = asyncio.create_task(world.start_world())
                    print("自动模拟已启动")
                else:
                    print("自动模拟已在运行")

            elif command == "stop":
                if auto_simulation:
                    auto_simulation = False
                    world.stop_world()
                    if simulation_task:
                        simulation_task.cancel()
                        simulation_task = None
                    print("自动模拟已停止")
                else:
                    print("自动模拟未在运行")

            elif command == "help":
                print("可用命令:")
                print("  status - 显示世界状态")
                print("  npc <name> - 显示特定NPC详情")
                print("  analyze <name> - 分析特定NPC")
                print("  event - 触发随机事件")
                print("  time - 推进时间")
                print("  start - 开始自动模拟")
                print("  stop - 停止自动模拟")
                print("  list - 列出所有NPC")
                print("  help - 显示帮助")
                print("  quit - 退出")

            else:
                print("未知命令，输入 'help' 查看可用命令")

        except KeyboardInterrupt:
            print("\n正在退出...")
            running = False
            if simulation_task:
                world.stop_world()
                simulation_task.cancel()
        except Exception as e:
            print(f"错误: {e}")


async def main():
    """主函数"""
    print("🎮 游戏NPC Agent演示系统")
    print("基于MengLong框架的自主生活NPC系统")
    print("=" * 50)

    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        print("请选择演示模式:")
        print("1. 单个NPC演示 - 观察单个NPC的自主决策")
        print("2. 世界模拟演示 - 观察多个NPC的互动")
        print("3. 配置世界演示 - 使用配置文件的高级功能")
        print("4. 交互式演示 - 手动控制和观察")

        choice = input("请输入选择 (1/2/3/4): ").strip()
        mode = {"1": "single", "2": "world", "3": "configured", "4": "interactive"}.get(
            choice, "single"
        )

    try:
        if mode == "single":
            await demo_single_npc()
        elif mode == "world":
            await demo_world_simulation()
        elif mode == "configured":
            await demo_configured_world()
        elif mode == "interactive":
            await interactive_demo()
        else:
            print("无效的模式，运行单个NPC演示")
            await demo_single_npc()

    except Exception as e:
        print(f"运行错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
