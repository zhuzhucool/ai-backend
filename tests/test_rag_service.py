import pytest

from app.services.rag_service import RagService, dedupe_results, extract_keywords


class FakeEmbedder:
    def __init__(self):
        self.texts = None

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.texts = texts
        return [[0.1, 0.2, 0.3]]


class FakeVectorStore:
    def __init__(self):
        self.keyword_calls = []
        self.vector_calls = []

    def keyword_search(self, keyword: str, owner_id: int, top_k: int = 5) -> list[dict]:
        self.keyword_calls.append((keyword, owner_id, top_k))
        return [{
            "text": "关键词命中文档",
            "source_file": "keyword.txt",
            "page_number": 1,
            "section_title": "关键词章节",
            "similarity": 1.0,
            "low_confidence": False,
        }]

    def search(self, query_embedding: list[float], owner_id: int, top_k: int = 5) -> list[dict]:
        self.vector_calls.append((query_embedding, owner_id, top_k))
        return [
            {
                "text": "关键词命中文档",
                "source_file": "keyword.txt",
                "page_number": 1,
                "section_title": "关键词章节",
                "similarity": 0.88,
                "low_confidence": False,
            },
            {
                "text": "向量命中文档",
                "source_file": "vector.txt",
                "page_number": 2,
                "section_title": "向量章节",
                "similarity": 0.76,
                "low_confidence": False,
            },
        ]


class FakeSession:
    added = []
    committed = False
    rolled_back = False
    raise_on_commit = False

    def __init__(self, engine):
        self.engine = engine

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def add(self, item):
        self.added.append(item)

    def commit(self):
        if self.raise_on_commit:
            raise RuntimeError("commit failed")
        type(self).committed = True

    def rollback(self):
        type(self).rolled_back = True

    @classmethod
    def reset(cls):
        cls.added = []
        cls.committed = False
        cls.rolled_back = False
        cls.raise_on_commit = False


def test_extract_keywords():
    result = extract_keywords("请问公司制度是什么？")

    print("提取关键词:", result)

    assert result == ["请问公司制度是什么？", "公司制度"]


def test_dedupe_results():
    results = dedupe_results([
        {"text": "重复内容", "source_file": "a.txt", "page_number": 1},
        {"text": "重复内容", "source_file": "a.txt", "page_number": 1},
        {"text": "新内容", "source_file": "b.txt", "page_number": 2},
    ])

    print("去重结果:", results)

    assert len(results) == 2


@pytest.mark.asyncio
async def test_rag_service_search(monkeypatch):
    FakeSession.reset()
    monkeypatch.setattr("app.services.rag_service.Session", FakeSession)
    embedder = FakeEmbedder()
    vector_store = FakeVectorStore()
    service = RagService(
        user_id=123,
        engine="fake_engine",
        embedder=embedder,
        vector_store=vector_store,
    )

    results = await service.search("请问公司制度是什么？", top_k=2)

    print("RAG 搜索结果:", results)
    print("写入日志:", FakeSession.added[0].model_dump())

    assert embedder.texts == ["请问公司制度是什么？"]
    assert vector_store.keyword_calls == [
        ("请问公司制度是什么？", 123, 2),
        ("公司制度", 123, 2),
    ]
    assert vector_store.vector_calls == [([0.1, 0.2, 0.3], 123, 2)]
    assert [result.text for result in results] == ["关键词命中文档", "向量命中文档"]
    assert results[0].similarity == 1.0

    log = FakeSession.added[0]
    assert log.user_id == 123
    assert log.query == "请问公司制度是什么？"
    assert log.top_k == 2
    assert log.results_count == 2
    assert log.top_similarity == 1.0
    assert FakeSession.committed is True


@pytest.mark.asyncio
async def test_rag_service_log_failure_does_not_break_search(monkeypatch):
    FakeSession.reset()
    FakeSession.raise_on_commit = True
    monkeypatch.setattr("app.services.rag_service.Session", FakeSession)
    service = RagService(
        user_id=123,
        engine="fake_engine",
        embedder=FakeEmbedder(),
        vector_store=FakeVectorStore(),
    )

    results = await service.search("公司制度", top_k=1)

    print("日志失败时的搜索结果:", results)
    print("日志是否 rollback:", FakeSession.rolled_back)

    assert len(results) == 1
    assert FakeSession.rolled_back is True
