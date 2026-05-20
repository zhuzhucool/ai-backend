import json
from app.agent.tools.base import BaseTool
import math

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "计算数学表达式。支持加减乘除、幂运算、三角函数等。"
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "数学表达式，如 '2 + 3 * 4' 或 'sqrt(16)'"
            }
        },
        "required": ["expression"]
    }
    


    async def execute(self, arguments: dict) -> str:
        expression = arguments["expression"]
        # 安全沙箱：只允许数学操作
        safe_env = {
            "__builtins__": {},
            "abs": abs, "round": round,
            "sqrt": math.sqrt, "pow": pow,
            "sin": math.sin, "cos": math.cos,
            "log": math.log, "pi": math.pi, "e": math.e
        }
        try:
            result = eval(expression, safe_env)
            return json.dumps({"result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})