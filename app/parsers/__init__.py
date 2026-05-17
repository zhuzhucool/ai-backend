from pathlib import Path
from app.parsers.docx_parser import DocxParser
from app.parsers.pdf_parser import PDFParser
from app.parsers.xlsx_parser import XlsxParser
from app.parsers.txt_parser import TxtParser

def get_parser(filename: str):
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return PDFParser()
    elif suffix == (".docx"):
        return DocxParser()
    elif suffix in (".xlsx", ".xls"):
        return XlsxParser()
    elif suffix == ".txt":
        return TxtParser()
    else:
        raise ValueError(f"不支持的文件类型: {suffix}")