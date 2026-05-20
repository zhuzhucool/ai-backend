import logging
import time
from dataclasses import dataclass

from sqlmodel import Session

from app.db.session import engine as default_engine
from app.models.retrieval_log import RetrievalLog
from app.rag.embedder import get_embedder
from app.rag.vectorstore import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class RagSearchResult:
    text: str
    source_file: str
    page_number: int | None
    similarity: float
    section_title: str | None = None
    low_confidence: bool = False

    def to_api_dict(self) -> dict:
        return {
            "text": self.text,
            "source_file": self.source_file,
            "page_number": self.page_number,
            "section_title": self.section_title,
            "similarity": self.similarity,
            "low_confidence": self.low_confidence,
        }


class RagService:
    def __init__(self, user_id: int, engine=default_engine, embedder=None, vector_store=None):
        self.user_id = user_id
        self.engine = engine
        self.embedder = embedder or get_embedder()
        self.vector_store = vector_store or VectorStore(engine)

    async def search(self, query: str, top_k: int = 3) -> list[RagSearchResult]:
        retrieval_start = time.perf_counter()

        try:
            keywords = extract_keywords(query)

            keyword_results = []
            for keyword in keywords:
                keyword_results.extend(
                    self.vector_store.keyword_search(keyword, self.user_id, top_k)
                )

            query_vec = await self.embedder.embed_texts([query])
            vector_results = self.vector_store.search(query_vec[0], self.user_id, top_k)

        except Exception:
            logger.exception(
                "rag search failed user_id=%s query=%s",
                self.user_id,
                query,
            )
            raise
        raw_results = dedupe_results(keyword_results + vector_results)[:top_k]
        results = [to_search_result(item) for item in raw_results]

        latency_ms = int((time.perf_counter() - retrieval_start) * 1000)
        self._write_retrieval_log(query, top_k, results, latency_ms)

        return results

    def _write_retrieval_log(
        self,
        query: str,
        top_k: int,
        results: list[RagSearchResult],
        latency_ms: int,
    ) -> None:
        top_similarity = max((result.similarity for result in results), default=None)

        with Session(self.engine) as session:
            try:
                session.add(RetrievalLog(
                    user_id=self.user_id,
                    query=query,
                    top_k=top_k,
                    results_count=len(results),
                    top_similarity=top_similarity,
                    latency_ms=latency_ms,
                ))
                session.commit()
            except Exception:
                session.rollback()
                logger.exception("failed to write retrieval log")


def to_search_result(item: dict) -> RagSearchResult:
    return RagSearchResult(
        text=item["text"],
        source_file=item["source_file"],
        page_number=item.get("page_number"),
        section_title=item.get("section_title"),
        similarity=item["similarity"],
        low_confidence=item.get("low_confidence", False),
    )


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
