from typing import Any, Dict
from pydantic import BaseModel

class ToolInfo(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
