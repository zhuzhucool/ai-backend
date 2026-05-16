import asyncio
import time

import httpx


BASE_URL = "http://127.0.0.1:18001"
CONCURRENT_REQUESTS = 5


async def send_chat(client: httpx.AsyncClient, index: int):
    started = time.perf_counter()
    response = await client.post(
        "/chat",
        json={
            "user_id": index,
            "message": f"请用一句话回复：这是第 {index} 个并发测试请求。",
            "session_id": index,
            "temperature": 0.7,
            "max_tokens": 100,
        },
    )
    elapsed = time.perf_counter() - started
    return index, response.status_code, elapsed, response.text[:200]


async def main():
    started = time.perf_counter()
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        results = await asyncio.gather(
            *(send_chat(client, index) for index in range(1, CONCURRENT_REQUESTS + 1)),
            return_exceptions=True,
        )

    total_elapsed = time.perf_counter() - started
    request_elapsed = []

    for result in results:
        if isinstance(result, Exception):
            print(f"请求失败: {type(result).__name__}: {result}")
            continue

        index, status_code, elapsed, body = result
        request_elapsed.append(elapsed)
        print(f"请求 {index}: status={status_code}, elapsed={elapsed:.2f}s, body={body}")

    print(f"总耗时: {total_elapsed:.2f}s")
    if request_elapsed:
        print(f"单个请求最长耗时: {max(request_elapsed):.2f}s")
        print("如果总耗时接近单个请求最长耗时，说明请求基本是并发执行；如果总耗时接近多个请求耗时相加，说明仍有明显阻塞。")


if __name__ == "__main__":
    asyncio.run(main())
