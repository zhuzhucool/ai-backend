import json
from decimal import Decimal

from app.agent.tools.base import BaseTool
from app.services.rag_service import RagService

class KnowledgeSearchTool(BaseTool):
    name = "search_knowledge"
    description = "从知识库中搜索相关信息。当用户问到公司制度、产品资料、文档内容时使用。"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词"},
            "top_k": {"type": "integer", "description": "返回结果数量，默认3"}
        },
        "required": ["query"]
    }

    def __init__(self, rag_service: RagService):
        self.rag = rag_service  # 注入阶段二的 RAG 服务

    async def execute(self, arguments: dict) -> str:
        query = arguments["query"]
        top_k = arguments.get("top_k", 3)
        results = await self.rag.search(query, top_k=top_k)
        return json.dumps({
            "results": [
                {
                    "content": r.text,
                    "source": r.source_file,
                    "page": r.page_number,
                    "score": float(r.similarity) if isinstance(r.similarity, Decimal) else r.similarity,
                }
                for r in results
            ]
        }, ensure_ascii=False)
