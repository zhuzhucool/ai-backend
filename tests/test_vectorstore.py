from app.db.session import engine
from app.rag.vectorstore import VectorStore


def make_vector(value: float) -> list[float]:
    return [value] * 1024


def test_add_embeddings_and_search():
    store = VectorStore(engine)

    # records = [
    #     {
    #         "doc_id": 999001,
    #         "owner_id": 123,
    #         "chunk_text": "衣服质量很好，穿起来很舒服",
    #         "chunk_index": 0,
    #         "source_file": "test.txt",
    #         "page_number": None,
    #         "section_title": "测试章节",
    #         "embedding": make_vector(0.1),
    #         "metadata_": {"test": True},
    #     },
    #     {
    #         "doc_id": 999001,
    #         "owner_id": 123,
    #         "chunk_text": "物流速度很快，第二天就到了",
    #         "chunk_index": 1,
    #         "source_file": "test.txt",
    #         "page_number": None,
    #         "section_title": "测试章节",
    #         "embedding": make_vector(0.2),
    #         "metadata_": {"test": True},
    #     },
    # ]

    # inserted_count = store.add_embeddings(records)

    results = store.search(
        query_embedding=make_vector(0.1),
        owner_id=123,
        top_k=1,
    )

    print(results)

    assert len(results) == 1
    assert results[0]["text"] == "衣服质量很好，穿起来很舒服"
    assert results[0]["source_file"] == "test.txt"
