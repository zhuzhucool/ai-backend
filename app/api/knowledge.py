from fastapi import APIRouter, Depends, HTTPException
from app.db.session import get_session, engine
from sqlmodel import Session
from app.core import config
import time
from app.services import llm
from app.rag.vectorstore import VectorStore
from app.rag.embedder import get_embedder
from app.core.security import verify_api_key, get_current_user_id
from app.models.retrieval_log import RetrievalLog
from app.schemas.knowledge import KnowledgeQueryResponse, KnowledgeSearchResponse
import logging

logger = logging.getLogger(__name__)
settings = config.Settings()
router = APIRouter()

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
    vector_store = VectorStore(engine)
    embedder = get_embedder()

    try:
        keywords = extract_keywords(query)
        keyword_results = []
        for keyword in keywords:
            keyword_results.extend(
                vector_store.keyword_search(keyword, current_user, top_k)
            )

        query_vec = await embedder.embed_texts([query])
        vector_results = vector_store.search(query_vec[0], current_user, top_k)
    except Exception as exc:
        logger.exception("knowledge search failed user_id=%s query=%s", current_user, query)
        raise HTTPException(status_code=503, detail="检索服务暂时不可用，请稍后重试") from exc

    results = dedupe_results(keyword_results + vector_results)[:top_k]
    return {"query": query, "results": results}


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
    db: Session = Depends(get_session)
):
    retrieval_start = time.perf_counter()

    # 1. 检索
    vector_store = VectorStore(engine)
    embedder = get_embedder()
    
    try:
        keywords = extract_keywords(query)

        keyword_results = []
        for keyword in keywords:
            keyword_results.extend(
                vector_store.keyword_search(keyword, current_user, top_k)
            )

        query_vec = await embedder.embed_texts([query])
        vector_results = vector_store.search(query_vec[0], current_user, top_k)
    except Exception as exc:
        logger.exception("knowledge retrieval failed user_id=%s query=%s", current_user, query)
        raise HTTPException(status_code=503, detail="检索服务暂时不可用，请稍后重试") from exc

    results = dedupe_results(keyword_results + vector_results)[:top_k]
    latency_ms = int((time.perf_counter() - retrieval_start) * 1000)
    top_similarity = max((r["similarity"] for r in results), default=None)

    try:
        db.add(RetrievalLog(
            user_id=current_user,
            query=query,
            top_k=top_k,
            results_count=len(results),
            top_similarity=top_similarity,
            latency_ms=latency_ms,
        ))
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("failed to write retrieval log")

    
    # 2. 检查置信度
    if all(r["low_confidence"] for r in results):
        return {
            "answer": "文档中未找到与您问题相关的内容，请确认已上传相关文档。",
            "sources": [],
            "confidence": "low"
        }
    
    # 3. 构造 prompt
    sources_text = "\n".join([
        f"【来源：{r['source_file']}"
        f"{' 第' + str(r['page_number']) + '页' if r['page_number'] else ''}】"
        f"\n{r['text']}"
        for r in results if not r["low_confidence"]
    ])
    
    prompt = RAG_PROMPT.format(sources=sources_text, question=query)
    
    # 4. 调用 LLM
    try:
        answer = await llm.llm_chat(prompt)
    except llm.LLMError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e

    # 5. 返回
    return {
        "answer": answer.choices[0].message.content,
        "sources": [{
            "file": r["source_file"],
            "page": r["page_number"],
            "similarity": r["similarity"]
        } for r in results if not r["low_confidence"]],
        "confidence": "high"
    }

def extract_keywords(query: str) -> list[str]:
    text = query.strip()
    stop_words = [
        "是谁", "是什么", "有哪些", "有什么", "介绍一下",
        "请问", "请介绍", "解释一下", "说明一下",
        "？", "?", "。", "."
    ]

    keywords = [text]

    keyword = text
    for word in stop_words:
        keyword = keyword.replace(word, "")

    keyword = keyword.strip()
    if keyword and keyword != text:
        keywords.append(keyword)

    return keywords


def dedupe_results(results: list[dict]) -> list[dict]:
    seen = set()
    deduped = []

    for item in results:
        # 同一段内容可能来自重复上传或混合检索，返回前只保留一次
        key = (
            item["text"],
            item["source_file"],
            item["page_number"],
        )
        if key in seen:
            continue

        seen.add(key)
        deduped.append(item)

    return deduped


