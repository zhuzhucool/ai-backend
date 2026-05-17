import asyncio

from app.rag.embedder import get_embedder


def test_embedder():
    embedder_client = get_embedder()

    input_embedder = asyncio.run(
        embedder_client.embed_texts(["衣服的质量杠杠的"])
    )

    print(input_embedder)

    assert len(input_embedder) == 1
