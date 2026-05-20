import asyncio
from app.agent.tools.knowledge_search import KnowledgeSearchTool
from app.services.rag_service import RagService


async def main():
    rag = RagService(user_id=123)   # 换成你本地实际有文档数据的用户
    tool = KnowledgeSearchTool(rag)

    result = await tool.execute({
        "query": "公司制度",
        "top_k": 3,
    })
    print(result)


asyncio.run(main())
