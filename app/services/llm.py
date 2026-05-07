from openai import OpenAI, APITimeoutError, AuthenticationError ,RateLimitError, APIConnectionError, APIStatusError, OpenAIError
from app.core import config

setting = config.Settings()

client = OpenAI(
    api_key=setting.OPENAI_API_KEY,
    base_url=setting.OPENAI_BASE_URL
)

class LLMError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def llm_chat(message :str, temperature: float, max_tokens: int):
    try:
        return client.chat.completions.create(
            model=setting.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": message},
            ],
            stream=False ,   # stream=False 非流式（一次性返回）、stream=True 流式（实时返回）
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=30.0
        )
    except APITimeoutError as e:
        raise LLMError("LLM 请求超时，请稍后重试", 504) from e
    except AuthenticationError as e:
        raise LLMError("LLM API Key 无效或已失效，请检查服务端配置", 502) from e
    except RateLimitError as e:
        raise LLMError("LLM 服务请求过于频繁，请稍后重试", 502) from e
    except APIConnectionError as e:
        raise LLMError("无法连接到 LLM 服务，请稍后重试", 502) from e
    except APIStatusError as e:
        raise LLMError(f"LLM 服务返回错误：{e.status_code}", 502) from e
    except OpenAIError as e:
        raise LLMError("LLM 服务调用失败", 502) from e