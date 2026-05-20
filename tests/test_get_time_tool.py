import json
from datetime import datetime

import pytest
import pytz

from app.agent.tools.get_time import GetCurrentTimeTool
from app.agent.tools.registry import ToolRegistry


def test_register_get_current_time_tool():
    registry = ToolRegistry()
    tool = GetCurrentTimeTool()

    registry.register(tool)

    print("已注册工具:", registry.list_tools())
    print("工具 schema:", registry.get_schemas())

    assert registry.list_tools() == ["get_current_time"]
    assert registry.get_schemas() == [tool.to_schema()]


@pytest.mark.asyncio
async def test_execute_get_current_time_default_timezone():
    registry = ToolRegistry()
    registry.register(GetCurrentTimeTool())

    result = await registry.execute("get_current_time", {})
    data = json.loads(result)

    print("默认时区时间结果:", result)

    parsed_datetime = datetime.fromisoformat(data["datetime"])
    assert "datetime" in data
    assert "formatted" in data
    assert parsed_datetime.tzinfo is not None
    assert parsed_datetime.utcoffset().total_seconds() == 8 * 60 * 60


@pytest.mark.asyncio
async def test_execute_get_current_time_custom_timezone():
    registry = ToolRegistry()
    registry.register(GetCurrentTimeTool())

    result = await registry.execute("get_current_time", {"timezone": "UTC"})
    data = json.loads(result)

    print("UTC 时间结果:", result)

    parsed_datetime = datetime.fromisoformat(data["datetime"])
    assert "datetime" in data
    assert "formatted" in data
    assert parsed_datetime.tzinfo is not None
    assert parsed_datetime.utcoffset().total_seconds() == 0


@pytest.mark.asyncio
async def test_execute_get_current_time_invalid_timezone():
    registry = ToolRegistry()
    registry.register(GetCurrentTimeTool())

    with pytest.raises(pytz.UnknownTimeZoneError):
        await registry.execute("get_current_time", {"timezone": "bad/timezone"})
