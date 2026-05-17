from app.rag.splitter import TextSplitter
from app.parsers.base import ParsedChunk


def test_split_text_with_overlap_when_no_separator():
    splitter = TextSplitter(chunk_size=10, chunk_overlap=2)

    result = splitter._split_text("abcdefghijklmnopqrstuvwxyz")

    assert result == [
        "abcdefghij",
        "ijklmnopqr",
        "qrstuvwxyz",
        "yz",
    ]


def test_split_keeps_metadata():
    splitter = TextSplitter(chunk_size=10, chunk_overlap=2)

    chunk = ParsedChunk(
        text="abcdefghijklmnopqrstuvwxyz",
        source_file="demo.txt",
        page_number=3,
        section_title="测试章节",
    )

    result = splitter.split([chunk])

    assert result[0].source_file == "demo.txt"
    assert result[0].page_number == 3
    assert result[0].section_title == "测试章节"


# python -m pytest tests/test_splitter.py
