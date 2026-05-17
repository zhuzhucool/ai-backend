from typing import Protocol
from openai import AsyncOpenAI
from app.core.config import settings



class Embedder(Protocol):
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...


class DashScopeEmbedder:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str = "text-embedding-v4",
        dimension: int = 1024,
    ):
        self.model = model
        self.dimension = dimension
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        response = await self.client.embeddings.create(
                    model=self.model,
                    input=texts,
                    dimensions=self.dimension,
                )

        return [item.embedding for item in response.data]



def get_embedder() -> Embedder:
    return DashScopeEmbedder(
        api_key=settings.EMBEDDING_KEY,
        base_url=settings.EMBEDDING_URL,
        model=settings.EMBEDDING_MODEL,
        dimension=settings.EMBEDDING_DIM,
    )
