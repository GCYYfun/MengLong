"""
基础转换器接口定义，为所有转换器提供通用结构。
"""

class BaseConverter:
    """
    所有转换器的基类，定义通用接口。
    """
    
    @staticmethod
    def convert_request(messages):
        """
        将MLong消息转换为特定模型API兼容的格式。
        
        Args:
            messages: MLong格式的消息列表
            
        Returns:
            转换后的适用于特定API的消息列表
        """
        raise NotImplementedError("子类必须实现此方法")
    
    @staticmethod
    def normalize_response(response):
        """
        将模型特定的响应格式标准化为MLong的响应格式。
        
        Args:
            response: 模型API的原始响应
            
        Returns:
            标准化后的MLong格式响应
        """
        raise NotImplementedError("子类必须实现此方法") 