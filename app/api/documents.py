from fastapi import APIRouter, Depends, HTTPException, UploadFile, Query, File
from app.schemas.document import DocumentUploadResponse, DocumentListResponse, DocumentDeleteResponse
from app.models.chat_message import ChatMessage
from app.models.document import Document
from app.db.session import get_session, engine
from sqlmodel import Session, select
from app.core.security import verify_api_key, get_current_user_id
from app.core import config
import time
from pathlib import Path
import uuid
from sqlalchemy import func
from app.parsers import get_parser
from app.rag.splitter import TextSplitter
from app.rag.embedder import get_embedder
from app.rag.vectorstore import VectorStore
import logging
from fastapi.concurrency import run_in_threadpool
from sqlmodel import delete
from app.models.document_embedding import DocumentEmbedding

logger = logging.getLogger(__name__)

settings = config.Settings()
router = APIRouter(tags=["Documents"])
UPLOAD_DIR = Path("uploads")
ALLOWED_EXTENSIONS = (".txt", ".pdf", ".docx", ".xlsx")
MAX_SIZE = 20 * 1024 * 1024  # 20MB

@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    summary="上传文档并建立 RAG 索引",
    description="保存上传文件，创建文档记录，解析文本并写入向量库。索引成功后 status 为 indexed。",
)
async def upload_document(file: UploadFile = File(...),
                          db: Session = Depends(get_session),
                          user_id: int = Depends(get_current_user_id)):
    # 开发环境需要考虑事务
    status = "uploaded"
    # 1. 校验文件名
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    # 2. 校验格式
    if not file.filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400, detail="仅支持 txt/pdf/docx/xlsx 格式")

    # 3. 读取内容并校验大小（用实际读取的字节判断，file.size 不一定可靠）
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制（最大 {MAX_SIZE // 1024 // 1024}MB）")

    # 4. 提取文本内容
    text_content = None
    UPLOAD_DIR.mkdir(exist_ok=True) #若路径不存在则创建
    safe_filename = f"{uuid.uuid4().hex}_{Path(file.filename).name}" #避免文件名重复
    file_path = UPLOAD_DIR / safe_filename #避免文件名重复
    
    #复制文件内容

    with file_path.open("wb") as buffer:
        buffer.write(content)

    document = Document(
            user_id=user_id,
            filename=file.filename,
            file_path=str(file_path),
            content_type=file.content_type,
            size=len(content),
            text_content=text_content,
            status=status
        )
    #上传数据库并返回id
    db.add(document)
    db.commit()
    db.refresh(document)
    
    try:
        parser = get_parser(file.filename)
        chunks = parser.parse(str(file_path), file.filename)

        splitter = TextSplitter()
        chunks = splitter.split(chunks)

        vector_store = VectorStore(engine)
        embedder = get_embedder()
        batch_size = 10

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            texts = [c.text for c in batch]
            embeddings = await embedder.embed_texts(texts)

            records = [{
                "doc_id": document.id,
                "owner_id": user_id,
                "chunk_text": c.text,
                "chunk_index": i + j,
                "source_file": c.source_file,
                "page_number": c.page_number,
                "section_title": c.section_title,
                "embedding": emb
            } for j, (c, emb) in enumerate(zip(batch, embeddings))]

            await run_in_threadpool(vector_store.add_embeddings, records)


        document.status = "indexed"
        db.add(document)
        db.commit()

    except Exception as exc:
        logger.exception("document indexing failed document_id=%s filename=%s", document.id, file.filename)
        document.status = "failed"
        db.add(document)
        db.commit()
        raise HTTPException(status_code=500, detail="文档索引失败") from exc
    
    return DocumentUploadResponse(
        document_id=document.id,
        filename=document.filename,
        status=document.status,
        chunks_count=len(chunks),
    )
 

@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="查询文档列表",
    description="按用户查询已上传文档，返回总数和分页后的文档列表。",
)
async def list_documents(
    user_id: int,
    db: Session = Depends(get_session),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    if user_id == None:
        return {"user_id": user_id, "error" : "当前user_id不存在"}
    # 查总数
    stmt = (
        select(func.count(Document.id))
        .where(Document.user_id == user_id)
    )
    total = db.exec(stmt).one()

    stmt = (
        select(Document)
        .where(Document.user_id == user_id)
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    documents = db.exec(stmt).all()

    return {
        "total": total,
        "documents": documents
    }

@router.delete(
    "/documents/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="删除文档",
    description="只能删除当前用户自己的文档，并同步删除对应的向量分片记录。",
)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    document = db.exec(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == user_id,
        )
    ).first()

    if document is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    # file_path = document.file_path  先不删

    try:
        db.exec(
            delete(DocumentEmbedding).where(
                DocumentEmbedding.doc_id == document.id,
                DocumentEmbedding.owner_id == user_id,
            )
        )
        db.exec(
            delete(Document).where(
                Document.id == document.id,
                Document.user_id == user_id,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return DocumentDeleteResponse(
        document_id=document_id,
        status="deleted",
    )

