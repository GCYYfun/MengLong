from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional


@dataclass
class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    role: MessageRole
    content: List[Dict]
