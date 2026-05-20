from fastapi import APIRouter, Depends, HTTPException
from app.core import config
from app.services import llm
from app.core.security import verify_api_key, get_current_user_id
from app.schemas.knowledge import KnowledgeQueryResponse, KnowledgeSearchResponse
from app.services.rag_service import RagService
import logging

logger = logging.getLogger(__name__)
settings = config.Settings()
router = APIRouter(tags=["Knowledge"])

RAG_PROMPT = """你是一个文档问答助手。请严格根据以下参考资料回答用户问题。
规则：
1. 只使用参考资料中的信息回答
2. 如果资料中没有相关信息，明确告知「文档中未找到相关内容」
3. 不要编造信息
4. 回答末尾标注引用来源

## 参考资料
{sources}

## 用户问题
{question}"""


@router.post(
    "/knowledge/search",
    response_model=KnowledgeSearchResponse,
    summary="知识库检索",
    description="只返回关键词和向量混合检索结果，不调用 LLM。",
)
async def knowledge_search(
    query: str,
    top_k: int = 5,
    current_user: int = Depends(get_current_user_id),
):
    try:
        results = await RagService(user_id=current_user).search(query, top_k)
    except Exception as exc:
        logger.exception("knowledge search failed user_id=%s query=%s", current_user, query)
        raise HTTPException(status_code=503, detail="检索服务暂时不可用，请稍后重试") from exc

    return {
        "query": query,
        "results": [result.to_api_dict() for result in results],
    }


@router.post(
    "/knowledge/query",
    response_model=KnowledgeQueryResponse,
    dependencies=[Depends(verify_api_key)],
    summary="知识库问答",
    description="先做关键词和向量混合检索，再基于命中的文档片段调用 LLM 生成回答。",
)
async def knowledge_query(
    query: str,
    top_k: int = 5,
    current_user: int = Depends(get_current_user_id),
):
    try:
        results = await RagService(user_id=current_user).search(query, top_k)
    except Exception as exc:
        logger.exception("knowledge retrieval failed user_id=%s query=%s", current_user, query)
        raise HTTPException(status_code=503, detail="检索服务暂时不可用，请稍后重试") from exc

    if all(result.low_confidence for result in results):
        return {
            "answer": "文档中未找到与您问题相关的内容，请确认已上传相关文档。",
            "sources": [],
            "confidence": "low"
        }

    sources_text = "\n".join([
        f"【来源：{result.source_file}"
        f"{' 第' + str(result.page_number) + '页' if result.page_number else ''}】"
        f"\n{result.text}"
        for result in results if not result.low_confidence
    ])

    prompt = RAG_PROMPT.format(sources=sources_text, question=query)

    try:
        answer = await llm.llm_chat(prompt)
    except llm.LLMError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e

    return {
        "answer": answer.choices[0].message.content,
        "sources": [{
            "file": result.source_file,
            "page": result.page_number,
            "similarity": result.similarity
        } for result in results if not result.low_confidence],
        "confidence": "high"
    }
