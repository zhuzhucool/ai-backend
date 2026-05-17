from docx import Document
from app.parsers.base import ParsedChunk

class DocxParser:
    def parse(self, file_path: str, filename: str) -> list[ParsedChunk]:
        doc = Document(file_path)
        chunks = []
        current_heading = None
        for para in doc.paragraphs:
            if para.style.name.startswith("Heading"):
                current_heading = para.text
            elif para.text.strip():
                chunks.append(ParsedChunk(
                    text=para.text,
                    source_file=filename,
                    page_number=None,
                    section_title=current_heading
                ))
        return chunks