import fitz  # pymupdf
from app.parsers.base import ParsedChunk

class PDFParser:
    def parse(self, file_path: str, filename: str) -> list[ParsedChunk]:
        doc = fitz.open(file_path)
        chunks = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                chunks.append(ParsedChunk(
                    text=text,
                    source_file=filename,
                    page_number=page_num + 1,
                    section_title=None
                ))
        doc.close()
        return chunks