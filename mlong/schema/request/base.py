from dataclasses import dataclass
from typing import Optional

@dataclass
class BaseRequest:
    """请求基础类型"""
    model_id: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop: Optional[list[str]] = None
    
    def validate(self) -> None:
        """验证请求参数
        
        Raises:
            ValueError: 当参数不合法时抛出
        """
        if not self.model_id:
            raise ValueError("model_id is required")
            
        if self.temperature is not None and not 0 <= self.temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")
            
        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
            
        if self.top_p is not None and not 0 <= self.top_p <= 1:
            raise ValueError("top_p must be between 0 and 1")