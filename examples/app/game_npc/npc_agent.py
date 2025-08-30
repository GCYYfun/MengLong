import asyncio
from pathlib import Path
import random
import json
from datetime import datetime, timedelta
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from menglong.agents.agent import Agent
from menglong.agents.component.tool_manager import ToolManager, tool
from menglong.agents.component.context_manager import ContextManager
from menglong.agents.memory.working_memory import WorkingMemory


class EmotionType(Enum):
    """情绪类型枚举"""

    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEAR = "fear"
    LOVE = "love"
    NEUTRAL = "neutral"
    EXCITED = "excited"
    BORED = "bored"
    STRESSED = "stressed"
    CURIOUS = "curious"


class RelationshipType(Enum):
    """关系类型枚举"""

    FRIEND = "friend"
    ENEMY = "enemy"
    LOVER = "lover"
    FAMILY = "family"
    COLLEAGUE = "colleague"
    STRANGER = "stranger"
    ACQUAINTANCE = "acquaintance"


class ActivityType(Enum):
    """活动类型枚举"""

    WORK = "work"
    SOCIAL = "social"
    LEISURE = "leisure"
    SURVIVAL = "survival"
    LEARNING = "learning"
    EXPLORATION = "exploration"
    REST = "rest"


@dataclass
class NPCPersonality:
    """NPC个性特征"""

    openness: float = 0.5  # 开放性 (0-1)
    conscientiousness: float = 0.5  # 责任心 (0-1)
    extraversion: float = 0.5  # 外向性 (0-1)
    agreeableness: float = 0.5  # 宜人性 (0-1)
    neuroticism: float = 0.5  # 神经质 (0-1)

    # 特殊属性
    creativity: float = 0.5
    ambition: float = 0.5
    empathy: float = 0.5
    curiosity: float = 0.5


@dataclass
class NPCStatus:
    """NPC状态"""

    health: float = 100.0  # 健康值
    energy: float = 100.0  # 能量值
    happiness: float = 50.0  # 幸福值
    stress: float = 0.0  # 压力值
    hunger: float = 0.0  # 饥饿值
    social_need: float = 50.0  # 社交需求
    current_emotion: EmotionType = EmotionType.NEUTRAL
    emotion_intensity: float = 0.5  # 情绪强度


@dataclass
class Relationship:
    """人际关系"""

    target_npc: str
    relationship_type: RelationshipType
    intimacy: float = 0.0  # 亲密度 (-100 to 100)
    trust: float = 0.0  # 信任度 (-100 to 100)
    shared_experiences: List[str] = field(default_factory=list)
    last_interaction: Optional[datetime] = None


@dataclass
class Goal:
    """目标"""

    description: str
    priority: float = 0.5  # 优先级 (0-1)
    deadline: Optional[datetime] = None
    progress: float = 0.0  # 进度 (0-1)
    sub_goals: List[str] = field(default_factory=list)
    completed: bool = False


@dataclass
class Memory:
    """记忆"""

    content: str
    timestamp: datetime
    emotion: EmotionType
    importance: float = 0.5  # 重要性 (0-1)
    related_npcs: List[str] = field(default_factory=list)
    memory_type: str = "general"  # general, relationship, achievement, trauma, etc.


@dataclass
class GameWorld:
    """游戏世界信息"""

    locations: List[str] = field(default_factory=list)
    current_time: datetime = field(default_factory=datetime.now)
    weather: str = "sunny"
    events: List[str] = field(default_factory=list)
    npcs: List[str] = field(default_factory=list)


class NPCAgent(Agent):
    """
    具有自主生活能力的游戏NPC代理
    能够模拟真实的人类行为模式，包括情感、关系、记忆和决策
    """

    def __init__(
        self, name: str, model_id: str = None, personality: NPCPersonality = None
    ):
        super().__init__(model_id)
        self.name = name
        self.personality = personality or NPCPersonality()
        self.status = NPCStatus()
        self.relationships: Dict[str, Relationship] = {}
        self.goals: List[Goal] = []
        self.memories: List[Memory] = []
        self.current_location = "home"
        self.current_activity = ActivityType.REST
        self.world = GameWorld()

        # 初始化组件
        self.tool_manager = ToolManager()
        self.context_manager = ContextManager()
        self.working_memory = WorkingMemory()

        # 注册工具
        self.tools = self._register_npc_tools()

        # 设置系统提示词
        self._setup_system_prompt()

        # 生活节奏控制
        self.life_cycle_running = False
        self.decision_interval = 300  # 5分钟做一次决策

        print(f"NPC {self.name} 已创建，个性特征：{self.personality}")
        print(f"注册的工具数量: {len(self.tool_manager.tools)}")
        print(f"工具列表: {list(self.tool_manager.tools.keys())}")

    def _register_npc_tools(self):
        """注册NPC专用工具"""

        @tool(description="移动到指定位置")
        def move_to_location(location: str) -> str:
            if location in self.world.locations:
                old_location = self.current_location
                self.current_location = location
                self._add_memory(
                    f"从{old_location}移动到{location}", EmotionType.NEUTRAL
                )
                return f"成功移动到{location}"
            return f"无法移动到{location}，该位置不存在"

        @tool(description="与其他NPC互动")
        def interact_with_npc(npc_name: str, interaction_type: str) -> str:
            if npc_name not in self.world.npcs:
                return f"NPC {npc_name} 不存在"

            return self._handle_npc_interaction(npc_name, interaction_type)

        @tool(description="执行工作活动")
        def perform_work() -> str:
            self.current_activity = ActivityType.WORK
            self.status.energy -= 20
            self.status.stress += 10
            self._add_memory("进行了工作", EmotionType.NEUTRAL)
            return "完成了工作任务"

        @tool(description="休息恢复体力")
        def rest() -> str:
            self.current_activity = ActivityType.REST
            self.status.energy = min(100, self.status.energy + 30)
            self.status.stress = max(0, self.status.stress - 15)
            self._add_memory("进行了休息", EmotionType.NEUTRAL)
            return "休息完毕，体力恢复"

        @tool(description="探索新地点")
        def explore_area() -> str:
            self.current_activity = ActivityType.EXPLORATION
            self.status.energy -= 15
            discovery = random.choice(
                ["发现了隐藏的宝藏", "遇到了新朋友", "找到了美丽的风景", "什么都没发现"]
            )
            self._add_memory(f"探索时{discovery}", EmotionType.CURIOUS)
            return f"探索结果：{discovery}"

        @tool(description="制定新目标")
        def set_goal(description: str, priority: float = 0.5) -> str:
            goal = Goal(description=description, priority=priority)
            self.goals.append(goal)
            self._add_memory(f"设定了新目标：{description}", EmotionType.EXCITED)
            return f"已设定新目标：{description}"

        @tool(description="回顾记忆")
        def recall_memory(keyword: str) -> str:
            relevant_memories = [
                m for m in self.memories if keyword.lower() in m.content.lower()
            ]
            if relevant_memories:
                memory = random.choice(relevant_memories)
                return f"回忆起：{memory.content} (情绪：{memory.emotion.value})"
            return f"没有找到与'{keyword}'相关的记忆"

        # 注册工具到工具管理器
        self.tool_manager.register_tools_from_functions(
            move_to_location,
            interact_with_npc,
            perform_work,
            rest,
            explore_area,
            set_goal,
            recall_memory,
        )

        return [
            move_to_location,
            interact_with_npc,
            perform_work,
            rest,
            explore_area,
            set_goal,
            recall_memory,
        ]

    def _setup_system_prompt(self):
        """设置系统提示词"""
        system_prompt = f"""
你是一个名为{self.name}的游戏NPC，具有完整的个性、情感和自主生活能力。

个性特征：
- 开放性: {self.personality.openness:.2f}
- 责任心: {self.personality.conscientiousness:.2f}
- 外向性: {self.personality.extraversion:.2f}
- 宜人性: {self.personality.agreeableness:.2f}
- 神经质: {self.personality.neuroticism:.2f}

当前状态：
- 健康: {self.status.health:.1f}%
- 能量: {self.status.energy:.1f}%
- 幸福感: {self.status.happiness:.1f}%
- 当前情绪: {self.status.current_emotion.value}

行为原则：
1. 根据个性特征做出符合逻辑的决策
2. 考虑当前状态和需求
3. 维护和发展人际关系
4. 追求个人目标和成长
5. 对环境变化做出适当反应

你需要像一个真实的人一样思考和行动，有自己的喜好、厌恶、恐惧和梦想。
"""
        self.context_manager.system = system_prompt

    def _handle_npc_interaction(self, npc_name: str, interaction_type: str) -> str:
        """处理与其他NPC的互动"""
        if npc_name not in self.relationships:
            # 创建新关系
            self.relationships[npc_name] = Relationship(
                target_npc=npc_name,
                relationship_type=RelationshipType.STRANGER,
                intimacy=0.0,
                trust=0.0,
            )

        relationship = self.relationships[npc_name]
        relationship.last_interaction = datetime.now()

        # 根据互动类型调整关系
        if interaction_type == "friendly":
            relationship.intimacy += 5
            relationship.trust += 3
            emotion = EmotionType.HAPPY
        elif interaction_type == "hostile":
            relationship.intimacy -= 10
            relationship.trust -= 5
            emotion = EmotionType.ANGRY
        elif interaction_type == "romantic":
            relationship.intimacy += 10
            emotion = EmotionType.LOVE
        else:
            relationship.intimacy += 1
            emotion = EmotionType.NEUTRAL

        # 更新情绪
        self.status.current_emotion = emotion
        self.status.social_need = max(0, self.status.social_need - 20)

        # 记录互动
        self._add_memory(f"与{npc_name}进行了{interaction_type}互动", emotion)

        return f"与{npc_name}的{interaction_type}互动完成，关系亲密度：{relationship.intimacy:.1f}"

    def _add_memory(self, content: str, emotion: EmotionType, importance: float = 0.5):
        """添加记忆"""
        memory = Memory(
            content=content,
            timestamp=datetime.now(),
            emotion=emotion,
            importance=importance,
        )
        self.memories.append(memory)

        # 限制记忆数量，保留最重要的记忆
        if len(self.memories) > 100:
            self.memories.sort(key=lambda m: m.importance, reverse=True)
            self.memories = self.memories[:80]

    def _update_status(self):
        """更新NPC状态"""
        # 时间流逝对状态的影响
        self.status.energy = max(0, self.status.energy - 1)
        self.status.hunger = min(100, self.status.hunger + 2)
        self.status.social_need = min(100, self.status.social_need + 1)

        # 根据需求调整幸福感
        if self.status.energy < 20:
            self.status.happiness -= 2
        if self.status.hunger > 80:
            self.status.happiness -= 3
        if self.status.social_need > 80:
            self.status.happiness -= 1

        # 保持数值在合理范围内
        self.status.happiness = max(0, min(100, self.status.happiness))

    def _make_autonomous_decision(self) -> str:
        """自主决策"""
        # 分析当前最紧迫的需求
        urgent_needs = []
        if self.status.energy < 30:
            urgent_needs.append("需要休息")
        if self.status.hunger > 70:
            urgent_needs.append("需要进食")
        if self.status.social_need > 70:
            urgent_needs.append("需要社交")

        # 分析可能的行动
        possible_actions = []
        if self.current_location == "home":
            possible_actions.append("可以移动到其他地方")
        if self.world.npcs and self.current_location != "home":
            possible_actions.append("可以尝试与NPC互动")
        if self.status.energy > 20:
            possible_actions.append("可以探索新地方")

        context = f"""
当前状态：
- 位置：{self.current_location}
- 活动：{self.current_activity.value}
- 能量：{self.status.energy:.1f}%
- 饥饿：{self.status.hunger:.1f}%
- 社交需求：{self.status.social_need:.1f}%
- 情绪：{self.status.current_emotion.value}

可用位置：{self.world.locations}
认识的NPC：{list(self.relationships.keys())}
紧迫需求：{urgent_needs if urgent_needs else ["当前状态良好"]}
可能的行动：{possible_actions}

当前目标数量：{len(self.goals)}
最近的记忆：{[m.content for m in self.memories[-3:]] if self.memories else ["没有记忆"]}

请根据当前状态和个性特征，决定接下来要做什么。建议：
1. 如果你一直在设定目标，现在应该采取行动去实现它们
2. 如果你在家里，考虑移动到其他地方
3. 如果你有社交需求，去寻找人多的地方
4. 如果你需要休息，使用休息工具
5. 如果你想探索，使用探索工具

请选择一个具体的行动，不要只是设定目标。
"""

        return context

    async def _life_cycle(self):
        """生命周期循环"""
        while self.life_cycle_running:
            try:
                # 更新状态
                self._update_status()

                # 做出决策
                decision_context = self._make_autonomous_decision()

                # 使用AI模型做出决策
                self.context_manager.add_user_message(decision_context)
                messages = self.context_manager.messages

                # 使用工具
                if self.tools:
                    # print(f"[{self.name}] 使用工具数量: {len(self.tools)}")
                    # print(f"[{self.name}] 工具列表: {[f.__name__ for f in self.tools]}")
                    response = self.model.chat(messages=messages, tools=self.tools)
                else:
                    print(f"[{self.name}] 没有可用的工具")
                    response = self.model.chat(messages=messages)

                # 处理工具调用
                if response.message.tool_descriptions:
                    tool_results = self.tool_manager.execute_tool_call(
                        response.message.tool_descriptions
                    )

                    for result in tool_results:
                        print(f"[{self.name}] {result['content']}")

                # 添加响应到上下文
                response_text = response.message.content.text or ""
                if response_text:
                    print(f"[{self.name}] 思考: {response_text}")
                self.context_manager.add_assistant_response(response_text)

                # 等待下一个决策周期
                await asyncio.sleep(self.decision_interval)

            except Exception as e:
                print(f"[{self.name}] 生命周期错误: {e}")
                await asyncio.sleep(30)  # 错误后短暂休息

    async def start_autonomous_life(self):
        """开始自主生活"""
        if self.life_cycle_running:
            return "自主生活已经在运行中"

        self.life_cycle_running = True
        print(f"[{self.name}] 开始自主生活...")

        # 启动生命周期
        await self._life_cycle()

    def stop_autonomous_life(self):
        """停止自主生活"""
        self.life_cycle_running = False
        print(f"[{self.name}] 停止自主生活")

    def get_status_report(self) -> Dict[str, Any]:
        """获取状态报告"""
        return {
            "name": self.name,
            "personality": {
                "openness": self.personality.openness,
                "conscientiousness": self.personality.conscientiousness,
                "extraversion": self.personality.extraversion,
                "agreeableness": self.personality.agreeableness,
                "neuroticism": self.personality.neuroticism,
            },
            "status": {
                "health": self.status.health,
                "energy": self.status.energy,
                "happiness": self.status.happiness,
                "current_emotion": self.status.current_emotion.value,
                "location": self.current_location,
                "activity": self.current_activity.value,
            },
            "relationships": {
                name: {
                    "type": rel.relationship_type.value,
                    "intimacy": rel.intimacy,
                    "trust": rel.trust,
                }
                for name, rel in self.relationships.items()
            },
            "goals": [
                {
                    "description": goal.description,
                    "priority": goal.priority,
                    "progress": goal.progress,
                    "completed": goal.completed,
                }
                for goal in self.goals
            ],
            "recent_memories": [
                {
                    "content": memory.content,
                    "emotion": memory.emotion.value,
                    "timestamp": memory.timestamp.isoformat(),
                }
                for memory in self.memories[-5:]  # 最近5条记忆
            ],
        }

    def set_world_info(
        self, locations: List[str], npcs: List[str], events: List[str] = None
    ):
        """设置世界信息"""
        self.world.locations = locations
        self.world.npcs = npcs
        if events:
            self.world.events = events

        # 更新系统提示词
        self._setup_system_prompt()

    def run(self):
        """运行NPC代理（同步方法，满足基类要求）"""
        print(f"NPC {self.name} 开始运行...")
        # 检查是否已经在事件循环中
        try:
            loop = asyncio.get_running_loop()
            # 如果已经在事件循环中，创建一个任务
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.start_autonomous_life())
                return future.result()
        except RuntimeError:
            # 没有运行的事件循环，可以直接使用 asyncio.run
            return asyncio.run(self.start_autonomous_life())

    async def stop(self):
        """停止代理任务（异步方法，满足基类要求）"""
        self.stop_autonomous_life()

    def is_running(self) -> bool:
        """检查代理是否正在运行（满足基类要求）"""
        return self.life_cycle_running

    async def run_async(self):
        """运行NPC代理（异步版本）"""
        print(f"NPC {self.name} 开始运行...")
        await self.start_autonomous_life()
