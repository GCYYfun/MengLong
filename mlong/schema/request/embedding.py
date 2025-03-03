from dataclasses import dataclass
from typing import List, Union, Optional
from .base import BaseRequest

@dataclass
class EmbeddingRequest(BaseRequest):
    """向量嵌入请求类型"""
    input: Union[str, List[str]]
    encoding_format: Optional[str] = None
    dimensions: Optional[int] = None
    
    def validate(self) -> None:
        """验证请求参数
        
        Raises:
            ValueError: 当参数不合法时抛出
        """
        super().validate()
        
        if not self.input:
            raise ValueError("input is required")
            
        if isinstance(self.input, list) and not all(isinstance(item, str) for item in self.input):
            raise ValueError("input列表中的所有元素必须是字符串类型")
            
        if self.dimensions is not None and self.dimensions <= 0:
            raise ValueError("dimensions必须是正整数")