import json
from decimal import Decimal

import pytest

from app.agent.tools.knowledge_search import KnowledgeSearchTool
from app.services.rag_service import RagSearchResult


class FakeRagService:
    async def search(self, query: str, top_k: int):
        return [
            RagSearchResult(
                text="质量检测流程内容",
                source_file="quality.pdf",
                page_number=3,
                similarity=Decimal("0.87"),
            )
        ]


@pytest.mark.asyncio
async def test_knowledge_search_serializes_decimal_similarity():
    tool = KnowledgeSearchTool(FakeRagService())

    result = json.loads(await tool.execute({"query": "质量检测流程", "top_k": 1}))

    print("知识库搜索工具结果:", result)

    assert result == {
        "results": [
            {
                "content": "质量检测流程内容",
                "source": "quality.pdf",
                "page": 3,
                "score": 0.87,
            }
        ]
    }
