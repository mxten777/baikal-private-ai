"""
Text Chunker - 텍스트 분할
"""
import re
from typing import List


def _is_table_line(line: str) -> bool:
    """탭 구분자가 있는 표 행 여부 판별"""
    return "\t" in line and len(line.split("\t")) >= 3


def _split_table_aware(text: str) -> List[str]:
    """표 영역을 행 단위로, 일반 텍스트는 단락 단위로 분리"""
    lines = text.split("\n")
    segments = []  # (is_table: bool, lines: List[str], header: str|None)

    i = 0
    while i < len(lines):
        line = lines[i]
        if _is_table_line(line):
            # 표 블록 수집
            table_lines = []
            header = line  # 첫 번째 표 행 = 헤더
            while i < len(lines) and (lines[i].strip() == "" or _is_table_line(lines[i])):
                if lines[i].strip():
                    table_lines.append(lines[i])
                i += 1
            segments.append(("table", table_lines, header))
        else:
            # 일반 텍스트 블록
            text_lines = []
            while i < len(lines) and not _is_table_line(lines[i]):
                text_lines.append(lines[i])
                i += 1
            if any(l.strip() for l in text_lines):
                segments.append(("text", text_lines, None))

    return segments


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """텍스트를 지정된 크기로 분할.
    표 영역은 행 단위로 묶어 헤더를 각 청크에 반복 삽입.
    일반 텍스트는 문장/단락 경계 기준으로 분할.
    """
    if not text or not text.strip():
        return []

    segments = _split_table_aware(text.strip())
    chunks = []

    for seg_type, seg_lines, header in segments:
        if seg_type == "table":
            # 표: 행 단위로 청크 구성, 헤더 항상 포함
            current_rows = [header] if header else []
            current_len = len(header) + 1 if header else 0

            for row in seg_lines:
                if row == header:
                    continue  # 헤더는 이미 추가됨
                row_len = len(row) + 1
                if current_len + row_len > chunk_size and len(current_rows) > 1:
                    chunks.append("\n".join(current_rows).strip())
                    # 다음 청크는 헤더부터 다시 시작
                    current_rows = [header] if header else []
                    current_len = len(header) + 1 if header else 0
                current_rows.append(row)
                current_len += row_len

            if current_rows and any(r != header for r in current_rows):
                chunks.append("\n".join(current_rows).strip())

        else:
            # 일반 텍스트: 기존 문자 기반 슬라이딩 윈도우
            seg_text = "\n".join(seg_lines).strip()
            if not seg_text:
                continue

            start = 0
            while start < len(seg_text):
                end = start + chunk_size
                if end >= len(seg_text):
                    chunk = seg_text[start:].strip()
                    if chunk:
                        chunks.append(chunk)
                    break

                boundary = seg_text.rfind("\n", start + chunk_size // 2, end)
                if boundary == -1:
                    boundary = seg_text.rfind(". ", start + chunk_size // 2, end)
                if boundary == -1:
                    boundary = seg_text.rfind(" ", start + chunk_size // 2, end)
                if boundary != -1:
                    end = boundary + 1

                chunk = seg_text[start:end].strip()
                if chunk:
                    chunks.append(chunk)
                start = end - overlap

    return [c for c in chunks if c]
