from openai import (
    AsyncOpenAI,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
    APIConnectionError,
    APIStatusError,
    OpenAIError,
)
import asyncio


RETRY_DELAYS = [0.5, 1.0]


class LLMError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class LLMService:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.model = model
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> dict:
        last_error = None

        for attempt in range(len(RETRY_DELAYS) + 1):
            try:
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "timeout": 60.0,
                }

                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"

                response = await self.client.chat.completions.create(**kwargs)
                choice = response.choices[0]
                message = choice.message

                return {
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                        for tool_call in (message.tool_calls or [])
                    ] or None,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                        "total_tokens": response.usage.total_tokens if response.usage else 0,
                    },
                    "model": response.model,
                    "finish_reason": choice.finish_reason,
                }

            except AuthenticationError as e:
                raise LLMError("LLM API Key 无效或已失效，请检查服务端配置", 502) from e

            except RateLimitError as e:
                last_error = e

            except APITimeoutError as e:
                last_error = e

            except APIConnectionError as e:
                last_error = e

            except APIStatusError as e:
                if e.status_code not in (500, 502, 503, 504):
                    raise LLMError(f"LLM 服务返回错误：{e.status_code}", 502) from e
                last_error = e

            except OpenAIError as e:
                raise LLMError("LLM 服务调用失败", 502) from e

            if attempt < len(RETRY_DELAYS):
                await asyncio.sleep(RETRY_DELAYS[attempt])

        if isinstance(last_error, APITimeoutError):
            raise LLMError("LLM 请求超时，请稍后重试", 504) from last_error

        if isinstance(last_error, RateLimitError):
            raise LLMError("LLM 服务请求过于频繁，请稍后重试", 502) from last_error

        if isinstance(last_error, APIConnectionError):
            raise LLMError("无法连接到 LLM 服务，请稍后重试", 502) from last_error

        if isinstance(last_error, APIStatusError):
            raise LLMError(f"LLM 服务返回错误：{last_error.status_code}", 502) from last_error

        raise LLMError("LLM 服务调用失败", 502)
