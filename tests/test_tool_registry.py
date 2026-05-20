import json
import pytest

from app.agent.tools.registry import ToolRegistry
from app.agent.tools.calculator import CalculatorTool


def test_register_calculator_tool():
    registry = ToolRegistry()
    tool = CalculatorTool()

    registry.register(tool)

    print("已注册工具:", registry.list_tools())
    print("工具 schema:", registry.get_schemas())

    assert registry.list_tools() == ["calculator"]
    assert registry.get_schemas() == [tool.to_schema()]


@pytest.mark.asyncio
async def test_execute_calculator_tool():
    registry = ToolRegistry()
    registry.register(CalculatorTool())

    result = await registry.execute("calculator", {"expression": "2 + 3 * 4"})

    print("计算结果:", result)

    assert json.loads(result) == {"result": 14}


@pytest.mark.asyncio
async def test_execute_calculator_math_function():
    registry = ToolRegistry()
    registry.register(CalculatorTool())

    result = await registry.execute("calculator", {"expression": "sqrt(16)"})

    print("函数计算结果:", result)

    assert json.loads(result) == {"result": 4.0}


@pytest.mark.asyncio
async def test_execute_calculator_invalid_expression():
    registry = ToolRegistry()
    registry.register(CalculatorTool())

    result = await registry.execute("calculator", {"expression": "1 / 0"})

    print("错误表达式结果:", result)

    assert "error" in json.loads(result)


@pytest.mark.asyncio
async def test_execute_unknown_tool():
    registry = ToolRegistry()

    result = await registry.execute("missing_tool", {})

    print("不存在工具时的结果:", result)

    assert json.loads(result) == {
        "error": "工具 missing_tool 不存在",
    }
