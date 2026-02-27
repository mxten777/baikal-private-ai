"""
Text Chunker - 텍스트 분할
"""
from typing import List


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """텍스트를 지정된 크기로 분할 (오버랩 포함)

    Args:
        text: 원본 텍스트
        chunk_size: 청크 크기 (문자 수)
        overlap: 오버랩 크기 (문자 수)

    Returns:
        청크 리스트
    """
    if not text or not text.strip():
        return []

    # 줄바꿈 정리
    text = text.strip()

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # 텍스트 끝을 넘지 않도록
        if end >= len(text):
            chunks.append(text[start:].strip())
            break

        # 문장 경계에서 자르기 시도 (마지막 마침표, 줄바꿈 찾기)
        boundary = text.rfind("\n", start + chunk_size // 2, end)
        if boundary == -1:
            boundary = text.rfind(". ", start + chunk_size // 2, end)
        if boundary == -1:
            boundary = text.rfind(" ", start + chunk_size // 2, end)
        if boundary != -1:
            end = boundary + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap

    return chunks
