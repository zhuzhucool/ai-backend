from sqlalchemy import text
from sqlmodel import Session
from app.models.document_embedding import DocumentEmbedding

class VectorStore:
    def __init__(self, engine):
        self.engine = engine
    #写入
    def add_embeddings(self, records: list[dict]):
        if not records:
            return 0
        
        with Session(self.engine) as session:
            try:
                for r in records:
                    embedding = DocumentEmbedding(
                        doc_id=r["doc_id"],
                        owner_id=r["owner_id"],
                        chunk_text=r["chunk_text"],
                        chunk_index=r["chunk_index"],
                        source_file=r["source_file"],
                        page_number=r.get("page_number"),
                        section_title=r.get("section_title"),
                        embedding=r["embedding"],
                        metadata_=r.get("metadata_"),
                    )
                    session.add(embedding)
                session.commit()
            except Exception:
                session.rollback()
                raise


    def search(
        self,
        query_embedding: list[float],
        owner_id: int,
        top_k: int = 5,
        threshold: float = 0.3,
    ) -> list[dict]:
        vector_text = "[" + ",".join(str(x) for x in query_embedding) + "]"

        with Session(self.engine) as session:
            results = session.exec(
                text("""
                    SELECT
                        chunk_text,
                        source_file,
                        page_number,
                        section_title,
                        1 - (embedding <=> CAST(:vec AS vector)) AS similarity
                    FROM document_embeddings
                    WHERE owner_id = :oid
                    ORDER BY embedding <=> CAST(:vec AS vector)
                    LIMIT :k
                """).bindparams(
                    vec=vector_text,
                    oid=owner_id,
                    k=top_k,
                )
            ).all()

        items = []

        for row in results:
            item = {
                "text": row.chunk_text,
                "source_file": row.source_file,
                "page_number": row.page_number,
                "section_title": row.section_title,
                "similarity": round(row.similarity, 4),
                "low_confidence": row.similarity < threshold,
            }
            items.append(item)

        return items

