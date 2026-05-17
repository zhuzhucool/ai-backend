from fastapi import APIRouter, Depends, HTTPException
from app.models.document import  Document
from app.db.session import get_session
from sqlmodel import Session, select
from app.core.security import verify_api_key, get_current_user_id
from app.core import config
import time
from app.services import llm

settings = config.Settings()
router = APIRouter()


@router.post("/knowledge/query", dependencies=[Depends(verify_api_key)])
async def knowledge_query(messages: str, document_id: int, db: Session = Depends(get_session), user_id: str = Depends(get_current_user_id)):
    if document_id == None:
        raise HTTPException(status_code=400, detail={
            "error": "bad_request",
            "document_id": "document_id 不能为空"
            })
    sql = (
        select(Document)
        .where(Document.id == document_id, Document.user_id == user_id)
    )
    document = db.exec(sql).first()
    if document is None:
        raise HTTPException(status_code=404, detail={
            "error": "not_found",
            "document_id": "文档不存在"
        })


    #日志记录
    start = time.perf_counter()
    response = None

    try:
        response = await llm.llm_chat(messages + "\n\n" +document.text_content, 0.7, 1024)

    except llm.LLMError as e:
        error_message = e.message
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
    finally:
        latency_ms = int((time.perf_counter() - start) * 1000)

    return {"answer": response.choices[0].message.content,
             "sources": [{
                "document_id": document_id,
                "filename": document.filename,
             }] 
            }

