from dataclasses import dataclass
from typing import Optional

@dataclass
class ParsedChunk:
    text: str                        # 提取的文本
    source_file: str                 # 原始文件名
    page_number: Optional[int]       # 页码（PDF 有，Word 可选）
    section_title: Optional[str]     # 章节标题（如有）
    chunk_type: str = "text"         # text / table / header