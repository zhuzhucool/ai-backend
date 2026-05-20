from abc import ABC, abstractmethod

class BaseTool(ABC):
    """工具基类 - 所有工具继承这个"""
    
    name: str           # 工具名，模型用这个来调用
    description: str    # 工具描述，告诉模型这个工具能干什么
    parameters: dict    # 参数 schema (JSON Schema 格式)
    
    def to_schema(self):
        """转成 OpenAI function calling 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
    
    @abstractmethod
    async def execute(self, arguments: dict) -> str:
        """实际执行逻辑，子类必须实现"""
        raise NotImplementedError