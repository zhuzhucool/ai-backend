import json
import logging

from app.agent.prompt import Prompt


logger = logging.getLogger(__name__)


class AgentLoop:
    """极简 Agent Loop"""

    MAX_ITERATIONS = 10

    def __init__(self, llm_service, tool_registry, memory=None, tool_log_writer=None):
        self.llm = llm_service
        self.tools = tool_registry
        self.memory = memory
        self.tool_log_writer = tool_log_writer

    async def run(self, user_message: str, session_id: int) -> dict:
        system_prompt = Prompt.build_system_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        logger.info("agent loop start session_id=%s", session_id)

        if self.memory:
            history = await self.memory.get_history(session_id)
            messages = [messages[0]] + history + [messages[1]]

        iterations = 0
        tool_calls_log = []
        answer = "抱歉，我尝试了多次但无法完成任务。"
        reached_max_iterations = True

        while iterations < self.MAX_ITERATIONS:
            iterations += 1
            logger.info("agent llm call start session_id=%s iteration=%s messages=%s", session_id, iterations, len(messages))
            response = await self.llm.chat(
                messages=messages,
                tools=self.tools.get_schemas(),
            )

            tool_calls = response.get("tool_calls") or []
            logger.info(
                "agent llm call finished session_id=%s iteration=%s tool_calls=%s",
                session_id,
                iterations,
                len(tool_calls),
            )

            if not tool_calls:
                answer = response.get("content", "")
                reached_max_iterations = False
                break

            assistant_message = self.build_assistant_message(response, tool_calls)
            if response.get("reasoning_content"):
                assistant_message["reasoning_content"] = response["reasoning_content"]

            messages.append(assistant_message)

            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                logger.info("agent tool call start session_id=%s iteration=%s tool=%s", session_id, iterations, tool_name)
                result = await self.execute_tool_call(tool_call)
                logger.info("agent tool call finished session_id=%s iteration=%s tool=%s", session_id, iterations, tool_name)

                tool_call_record = {
                    "tool": tool_name,
                    "arguments": result["arguments"],
                    "result": result["content"],
                    "iteration": iterations,
                }
                tool_calls_log.append(tool_call_record)
                await self.save_tool_log(session_id, tool_call_record)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result["content"],
                })

        if reached_max_iterations:
            logger.warning("agent loop reached max iterations session_id=%s iterations=%s", session_id, iterations)
        else:
            logger.info("agent loop finished session_id=%s iterations=%s", session_id, iterations)

        if self.memory:
            await self.memory.save(session_id, user_message, answer)

        return {
            "answer": answer,
            "iterations": iterations,
            "tool_calls": tool_calls_log,
        }

    def build_assistant_message(self, response: dict, tool_calls: list[dict]) -> dict:
        return {
            "role": "assistant",
            "content": response.get("content", ""),
            "tool_calls": tool_calls,
        }

    async def save_tool_log(self, session_id: int, tool_call_record: dict) -> None:
        if not self.tool_log_writer:
            return

        try:
            await self.tool_log_writer.save(session_id, tool_call_record)
        except Exception:
            logger.exception(
                "agent tool log save failed session_id=%s iteration=%s tool=%s",
                session_id,
                tool_call_record["iteration"],
                tool_call_record["tool"],
            )

    async def execute_tool_call(self, tool_call: dict) -> dict:
        tool_name = tool_call["function"]["name"]
        raw_arguments = tool_call["function"].get("arguments") or "{}"

        try:
            arguments = json.loads(raw_arguments)
        except json.JSONDecodeError as exc:
            logger.exception("agent tool arguments json decode failed tool=%s", tool_name)
            return {
                "arguments": {},
                "content": json.dumps({"error": f"工具参数不是合法 JSON：{exc.msg}"}, ensure_ascii=False),
            }

        try:
            content = await self.tools.execute(tool_name, arguments)
        except Exception as exc:
            logger.exception("agent tool execute failed tool=%s", tool_name)
            content = json.dumps({"error": str(exc)}, ensure_ascii=False)

        return {
            "arguments": arguments,
            "content": content,
        }
