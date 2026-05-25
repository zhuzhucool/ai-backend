import json
import logging

from sqlalchemy.exc import SQLAlchemyError

from app.models.agent_log import AgentToolLog


logger = logging.getLogger(__name__)


class AgentToolLogWriterError(Exception):
    pass


class AgentToolLogWriter:
    def __init__(self, db_session, user_id: int):
        self.db = db_session
        self.user_id = user_id

    async def save(self, session_id: int, tool_call: dict) -> None:
        success, error_message = self.parse_result_status(tool_call["result"])
        log = AgentToolLog(
            session_id=session_id,
            user_id=self.user_id,
            tool=tool_call["tool"],
            arguments=json.dumps(tool_call["arguments"], ensure_ascii=False),
            result=tool_call["result"],
            iteration=tool_call["iteration"],
            success=success,
            error_message=error_message,
        )

        try:
            self.db.add(log)
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.exception("Failed to save agent tool log")
            raise AgentToolLogWriterError("保存工具调用日志失败") from exc

    def parse_result_status(self, result: str) -> tuple[bool, str | None]:
        try:
            parsed_result = json.loads(result)
        except json.JSONDecodeError:
            return True, None

        if isinstance(parsed_result, dict) and "error" in parsed_result:
            return False, str(parsed_result["error"])

        return True, None
