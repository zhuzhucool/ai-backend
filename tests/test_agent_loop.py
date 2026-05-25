import json

import pytest

from app.agent.loop import AgentLoop
from app.agent.tools.calculator import CalculatorTool
from app.agent.tools.get_time import GetCurrentTimeTool
from app.agent.tools.registry import ToolRegistry
from app.agent.prompt import Prompt


class FakeLLM:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    async def chat(self, messages, tools):
        self.calls.append({"messages": messages, "tools": tools})
        return self.responses[len(self.calls) - 1]


class FakeMemory:
    def __init__(self):
        self.saved = []

    async def get_history(self, session_id):
        return [
            {"role": "user", "content": "之前的问题"},
            {"role": "assistant", "content": "之前的回答"},
        ]

    async def save(self, session_id, user_message, answer):
        self.saved.append({
            "session_id": session_id,
            "user_message": user_message,
            "answer": answer,
        })


def build_registry():
    registry = ToolRegistry()
    registry.register(GetCurrentTimeTool())
    registry.register(CalculatorTool())
    return registry


def tool_call(call_id, name, arguments):
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": name,
            "arguments": json.dumps(arguments),
        },
    }
def pretty_agent_result(result):
    print("\nAgent 运行结果")
    print(f"answer: {result['answer']}")
    print(f"iterations: {result['iterations']}")

    print("tool_calls:")
    for call in result["tool_calls"]:
        parsed_result = json.loads(call["result"])
        print(
            f"  - iteration={call['iteration']} "
            f"tool={call['tool']} "
            f"arguments={call['arguments']} "
            f"result={parsed_result}"
        )


# @pytest.mark.asyncio
# async def test_run_answers_directly_without_tool_calls():
#     llm = FakeLLM([
#         {
#             "content": "你好，我可以帮你处理问题。",
#             "tool_calls": None,
#         }
#     ])
#     memory = FakeMemory()
#     agent = AgentLoop(llm, build_registry(), memory)

#     result = await agent.run("你好", "session-1")

#     print("Agent 直接回答结果:", result)

#     assert result == {
#         "answer": "你好，我可以帮你处理问题。",
#         "iterations": 1,
#         "tool_calls": [],
#     }
#     assert memory.saved == [
#         {
#             "session_id": "session-1",
#             "user_message": "你好",
#             "answer": "你好，我可以帮你处理问题。",
#         }
#     ]
#     assert llm.calls[0]["messages"] == [
#         {"role": "system", "content": Prompt.build_system_prompt()},
#         {"role": "user", "content": "之前的问题"},
#         {"role": "assistant", "content": "之前的回答"},
#         {"role": "user", "content": "你好"},
#     ]


@pytest.mark.asyncio
async def test_run_calls_calculator_then_returns_answer():
    llm = FakeLLM([
        {
            "content": "",
            "tool_calls": [tool_call("call_1", "calculator", {"expression": "123*456+789"})],
        },
        {
            "content": "计算结果是 56877。",
            "tool_calls": None,
        },
    ])
    agent = AgentLoop(llm, build_registry())

    result = await agent.run("计算 123*456+789", "session-1")

    print("Agent 计算工具结果:", result)
    print("=" * 50)
    print("第二轮模型消息列表:", llm.calls[1]["messages"])
    print("=" * 50)
    assert result["answer"] == "计算结果是 56877。"
    assert result["iterations"] == 2
    assert result["tool_calls"] == [
        {
            "tool": "calculator",
            "arguments": {"expression": "123*456+789"},
            "result": json.dumps({"result": 56877}),
            "iteration": 1,
        }
    ]
    assert llm.calls[1]["messages"][-1] == {
        "role": "tool",
        "tool_call_id": "call_1",
        "content": json.dumps({"result": 56877}),
    }


# @pytest.mark.asyncio
# async def test_run_calls_get_current_time_then_returns_answer():
#     llm = FakeLLM([
#         {
#             "content": "",
#             "tool_calls": [tool_call("call_1", "get_current_time", {"timezone": "Asia/Shanghai"})],
#         },
#         {
#             "content": "现在是工具返回的北京时间。",
#             "tool_calls": None,
#         },
#     ])
#     agent = AgentLoop(llm, build_registry())

#     result = await agent.run("现在几点", "session-1")
#     tool_result = json.loads(result["tool_calls"][0]["result"])
#     print("=" * 50)
#     print("Agent 时间工具结果:", result)
#     print("=" * 50)
#     assert result["answer"] == "现在是工具返回的北京时间。"
#     assert result["iterations"] == 2
#     assert result["tool_calls"][0]["tool"] == "get_current_time"
#     assert "datetime" in tool_result
#     assert "formatted" in tool_result


@pytest.mark.asyncio
async def test_run_stops_after_max_iterations():
    llm = FakeLLM([
        {
            "content": "",
            "tool_calls": [tool_call(f"call_{index}", "calculator", {"expression": "1+1"})],
        }
        for index in range(AgentLoop.MAX_ITERATIONS)
    ])
    agent = AgentLoop(llm, build_registry())

    result = await agent.run("一直调用工具", "session-1")

    pretty_agent_result(result)


    assert result["answer"] == "抱歉，我尝试了多次但无法完成任务。"
    assert result["iterations"] == AgentLoop.MAX_ITERATIONS
    assert len(result["tool_calls"]) == AgentLoop.MAX_ITERATIONS
    assert len(llm.calls) == AgentLoop.MAX_ITERATIONS


# @pytest.mark.asyncio
# async def test_run_records_tool_argument_error_as_tool_result():
#     llm = FakeLLM([
#         {
#             "content": "",
#             "tool_calls": [
#                 {
#                     "id": "call_1",
#                     "type": "function",
#                     "function": {
#                         "name": "calculator",
#                         "arguments": "{bad json",
#                     },
#                 }
#             ],
#         },
#         {
#             "content": "工具参数格式有误。",
#             "tool_calls": None,
#         },
#     ])
#     agent = AgentLoop(llm, build_registry())

#     result = await agent.run("算一下", "session-1")

#     print("Agent 工具参数错误结果:", result)

#     assert result["answer"] == "工具参数格式有误。"
#     assert result["tool_calls"][0]["arguments"] == {}
#     assert "工具参数不是合法 JSON" in result["tool_calls"][0]["result"]
