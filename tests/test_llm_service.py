# 引入 SimpleNamespace 用来模拟 SDK 返回对象，避免真实请求模型服务。
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

# 测试目标是 LLMService，不测试 OpenAI SDK 本身。
from app.services.llm import LLMService


class TestLLMService:
    # 这个测试验证普通聊天返回值会被转换成项目内部使用的 dict。
    # @pytest.mark.asyncio
    # async def test_chat_returns_content_usage_and_model(self):
    #     service = LLMService(
    #         api_key="sk-5c23515e80c749bba6768a92e3ae7ff8",
    #         base_url="https://api.deepseek.com/v1",
    #         model="deepseek-v4-flash",
    #     )
    #     # mock 掉 SDK 调用，这样测试只关注 LLMService 的封装逻辑。
    #     service.client.chat.completions.create = AsyncMock(
    #         return_value=SimpleNamespace(
    #             model="deepseek-v4-flash",
    #             choices=[
    #                 SimpleNamespace(
    #                     finish_reason="stop",
    #                     message=SimpleNamespace(
    #                         content="测试回复",
    #                         tool_calls=None,
    #                     ),
    #                 )
    #             ],
    #             # usage 模拟 token 统计，用来验证日志和成本统计字段。
    #             usage=SimpleNamespace(
    #                 prompt_tokens=10,
    #                 completion_tokens=5,
    #                 total_tokens=15,
    #             ),
    #         )
    #     )

    #     result = await service.chat(
    #         messages=[{"role": "user", "content": "你好"}],
    #         temperature=0.2,
    #         max_tokens=128,
    #     )

    #     # 打印结果是为了本地运行测试时能直接看到封装后的结构。
    #     print("LLM 普通聊天结果:", result)

    #     service.client.chat.completions.create.assert_awaited_once_with(
    #         model="deepseek-v4-flash",
    #         messages=[{"role": "user", "content": "你好"}],
    #         stream=False,
    #         temperature=0.2,
    #         max_tokens=128,
    #         timeout=60.0,
    #     )
    #     # 这里断言的是项目对外使用的数据结构，不依赖 SDK 原始对象。
    #     assert result == {
    #         "content": "测试回复",
    #         "tool_calls": None,
    #         "usage": {
    #             "prompt_tokens": 10,
    #             "completion_tokens": 5,
    #             "total_tokens": 15,
    #         },
    #         "model": "deepseek-v4-flash",
    #         "finish_reason": "stop",
    #     }

    # 这个测试验证传入 tools 后，模型返回的 tool_calls 能被正确提取。

    
    @pytest.mark.asyncio
    async def test_chat_passes_tools_and_returns_tool_calls(self):
        service = LLMService(
            api_key="扫你妈的key",
            base_url="https://api.deepseek.com/v1",
            model="deepseek-v4-flash",
        )
        # tools 是发给模型看的函数说明，真正执行工具的是后端代码。
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "计算表达式",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {"type": "string"},
                        },
                        "required": ["expression"],
                    },
                },
            }
        ]
        # 这里模拟模型决定调用 calculator，而不是直接给最终文本回答。
        service.client.chat.completions.create = AsyncMock(
            return_value=SimpleNamespace(
                model="test-model",
                choices=[
                    SimpleNamespace(
                        finish_reason="tool_calls",
                        message=SimpleNamespace(
                            content=None,
                            tool_calls=[
                                SimpleNamespace(
                                    id="call_123",
                                    type="function",
                                    function=SimpleNamespace(
                                        name="calculator",
                                        arguments='{"expression":"2+3"}',
                                    ),
                                )
                            ],
                        ),
                    )
                ],
                # tool_calls 也会消耗 token，所以这里保留 usage 断言。
                usage=SimpleNamespace(
                    prompt_tokens=20,
                    completion_tokens=7,
                    total_tokens=27,
                ),
            )
        )

        result = await service.chat(
            messages=[{"role": "user", "content": "算一下 2+3"}],
            tools=tools,
        )

        # 这里看到的是第一轮模型输出，还不是工具执行后的最终回答。
        print("LLM Tool Calling 结果:", result)

        service.client.chat.completions.create.assert_awaited_once_with(
            model="deepseek-v4-flash",
            messages=[{"role": "user", "content": "算一下 2+3"}],
            stream=False,
            temperature=0.7,
            max_tokens=1024,
            timeout=60.0,
            tools=tools,
            tool_choice="auto",
        )
        # content 为空是正常的，因为模型这一轮选择了调用工具。
        assert result["content"] == ""
        assert result["tool_calls"] == [
            {
                "id": "call_123",
                "type": "function",
                "function": {
                    "name": "calculator",
                    "arguments": '{"expression":"2+3"}',
                },
            }
        ]
        # usage 用于后续写入 llm_logs 或统计模型成本。
        assert result["usage"] == {
            "prompt_tokens": 20,
            "completion_tokens": 7,
            "total_tokens": 27,
        }
        assert result["finish_reason"] == "tool_calls"
