from app.parsers.base import ParsedChunk


# todo 后续实现分块重叠 https://linux.do/t/topic/2187051
class TextSplitter:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", "。", ". ", " "]
    
    def split(self, chunks: list[ParsedChunk]) -> list[ParsedChunk]:
        result = []
        for chunk in chunks:
            sub_chunks = self._split_text(chunk.text)
            for text in sub_chunks:
                result.append(ParsedChunk(
                    text=text,
                    source_file=chunk.source_file,
                    page_number=chunk.page_number,
                    section_title=chunk.section_title
                ))
        return result
    
    def _split_text(self, text: str) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []
        for sep in self.separators:
            if sep in text:
                parts = text.split(sep)
                chunks, current = [], ""
                for part in parts:
                    if len(current) + len(part) + len(sep) <= self.chunk_size:
                        current += part + sep
                    else:
                        if current.strip():
                            chunks.append(current.strip())
                        current = part + sep
                if current.strip():
                    chunks.append(current.strip())
                return chunks
        result = []

        step = self.chunk_size - self.chunk_overlap

        for i in range(0, len(text), step):
            chunk = text[i:i + self.chunk_size]
            result.append(chunk)

        return result
