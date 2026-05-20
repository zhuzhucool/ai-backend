from datetime import datetime
import pytz
import json
from app.agent.tools.base import BaseTool

class GetCurrentTimeTool(BaseTool):
    name = "get_current_time"
    description = "获取当前日期和时间"
    parameters = {
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "description": "时区，如 Asia/Shanghai，默认中国时区"
            }
        }
    }
    
    async def execute(self, arguments: dict) -> str:
        tz_name = arguments.get("timezone", "Asia/Shanghai")
        tz = pytz.timezone(tz_name)
        now = datetime.now(tz)
        return json.dumps({
            "datetime": now.isoformat(),
            "formatted": now.strftime("%Y-%m-%d %H:%M:%S")
        })