from app.parsers.base import ParsedChunk


class TxtParser:
    def parse(self, file_path: str, filename: str) -> list[ParsedChunk]:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        if not text.strip():
            return []

        return [
            ParsedChunk(
                text=text,
                source_file=filename,
                page_number=None,
                section_title=None,
            )
        ]
