import json

class ToolRegistry:
    """工具注册表 - Agent 的工具箱"""
    
    def __init__(self):
        self._tools = {}      # name -> tool 实例
        self._schemas = []    # 给模型看的 tools schema 列表
    
    def register(self, tool):
        """注册一个工具"""
        self._tools[tool.name] = tool
        self._schemas.append(tool.to_schema())
    
    def get_schemas(self):
        """返回所有工具 schema，发给模型用"""
        return self._schemas
    
    def list_tools(self):
        """列出所有已注册工具名"""
        return list(self._tools.keys())
    
    async def execute(self, tool_name: str, arguments: dict) -> str:
        """执行指定工具"""
        if tool_name not in self._tools:
            return json.dumps({"error": f"工具 {tool_name} 不存在"})
        return await self._tools[tool_name].execute(arguments)

