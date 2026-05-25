import json
from app.agent.prompt import Prompt

class AgentLoop:
    """极简 Agent Loop"""

    MAX_ITERATIONS = 10

    def __init__(self, llm_service, tool_registry, memory=None):
        self.llm = llm_service
        self.tools = tool_registry
        self.memory = memory

    async def run(self, user_message: str, session_id: str) -> dict:
        system_prompt = Prompt.build_system_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        if self.memory:
            history = await self.memory.get_history(session_id)
            messages = [messages[0]] + history + [messages[1]]

        iterations = 0
        tool_calls_log = []

        while iterations < self.MAX_ITERATIONS:
            iterations += 1
            response = await self.llm.chat(
                messages=messages,
                tools=self.tools.get_schemas(),
            )
            tool_calls = response.get("tool_calls") or []

            if not tool_calls:
                answer = response.get("content", "")
                if self.memory:
                    await self.memory.save(session_id, user_message, answer)
                return {
                    "answer": answer,
                    "iterations": iterations,
                    "tool_calls": tool_calls_log,
                }

            messages.append(self.build_assistant_message(response, tool_calls))

            for tool_call in tool_calls:
                result = await self.execute_tool_call(tool_call)
                tool_calls_log.append({
                    "tool": tool_call["function"]["name"],
                    "arguments": result["arguments"],
                    "result": result["content"],
                    "iteration": iterations,
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result["content"],
                })

        return {
            "answer": "抱歉，我尝试了多次但无法完成任务。",
            "iterations": iterations,
            "tool_calls": tool_calls_log,
        }


    def build_assistant_message(self, response: dict, tool_calls: list[dict]) -> dict:
        return {
            "role": "assistant",
            "content": response.get("content") or None,
            "tool_calls": tool_calls,
        }

    async def execute_tool_call(self, tool_call: dict) -> dict:
        tool_name = tool_call["function"]["name"]
        raw_arguments = tool_call["function"].get("arguments") or "{}"

        try:
            arguments = json.loads(raw_arguments)
        except json.JSONDecodeError as exc:
            return {
                "arguments": {},
                "content": json.dumps({"error": f"工具参数不是合法 JSON：{exc.msg}"}, ensure_ascii=False),
            }

        try:
            content = await self.tools.execute(tool_name, arguments)
        except Exception as exc:
            content = json.dumps({"error": str(exc)}, ensure_ascii=False)

        return {
            "arguments": arguments,
            "content": content,
        }
