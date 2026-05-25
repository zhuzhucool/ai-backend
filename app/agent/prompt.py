
class Prompt():

    def build_system_prompt() -> str:
        return (
            "你是一个可以使用工具的 AI 助手。"
            "需要实时信息或计算时调用工具；工具返回后，根据结果回答用户。"
        )