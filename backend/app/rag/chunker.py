"""
Text Chunker - 텍스트 분할
"""
import re
from typing import List

import numpy as np


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """두 벡터의 코사인 유사도 계산"""
    a_arr = np.array(a, dtype=np.float32)
    b_arr = np.array(b, dtype=np.float32)
    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / (norm_a * norm_b))


def split_into_paragraphs(text: str, min_len: int = 15) -> List[str]:
    """텍스트를 단락 단위로 분할.
    - 이중 줄바꿈 기준 1차 분리
    - 800자 초과 단락은 단일 줄바꿈으로 추가 분리
    - 표 행이 포함된 단락은 하나로 유지
    """
    paragraphs = re.split(r'\n\s*\n', text)
    result = []
    for p in paragraphs:
        p = p.strip()
        if not p or len(p) < min_len:
            continue
        if len(p) > 800 and not _is_table_line(p.split('\n')[0]):
            lines = [l.strip() for l in p.split('\n') if l.strip() and len(l.strip()) >= min_len]
            result.extend(lines)
        else:
            result.append(p)
    return result if result else [text.strip()]


def semantic_chunk_with_embeddings(
    paragraphs: List[str],
    embeddings: List[List[float]],
    similarity_threshold: float = 0.75,
    max_chunk_size: int = 500,
    min_chunk_size: int = 80,
) -> List[str]:
    """사전 계산된 임베딩을 사용해 시맨틱 청킹 수행.

    인접 단락 임베딩의 코사인 유사도가 임계값 아래로 떨어지면 청크 경계로 판단.
    max_chunk_size 초과 시 강제 분할, min_chunk_size 미만이면 분할 보류.
    """
    if not paragraphs:
        return []
    if len(paragraphs) == 1:
        return paragraphs

    chunks: List[str] = []
    current: List[str] = [paragraphs[0]]
    current_size: int = len(paragraphs[0])

    for i in range(1, len(paragraphs)):
        sim = _cosine_similarity(embeddings[i - 1], embeddings[i])
        next_size = current_size + len(paragraphs[i]) + 1

        semantic_break = sim < similarity_threshold and current_size >= min_chunk_size
        size_break = next_size > max_chunk_size

        if semantic_break or size_break:
            chunks.append("\n".join(current))
            current = [paragraphs[i]]
            current_size = len(paragraphs[i])
        else:
            current.append(paragraphs[i])
            current_size = next_size

    if current:
        chunks.append("\n".join(current))

    return chunks


def _is_table_line(line: str) -> bool:
    """탭 구분자가 있는 표 행 여부 판별"""
    return "\t" in line and len(line.split("\t")) >= 3


def split_table_aware(text: str) -> List[str]:
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

    segments = split_table_aware(text.strip())
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


def table_chunk_to_nl(chunk: str) -> str:
    """표 청크를 자연어 문장으로 변환 (임베딩 품질 향상).
    탭 구분 행이 없으면 원본 그대로 반환.

    예시 변환:
      입력:  "이름\t금액\t연도\n홍길동\t5000\t2024"
      출력:  "이름이 홍길동이고 금액이 5000이며 연도는 2024입니다."
    """
    lines = [l for l in chunk.strip().split("\n") if l.strip()]
    if len(lines) < 2:
        return chunk

    # 헤더 행 (탭 구분) 감지
    header_line = lines[0]
    if "\t" not in header_line:
        return chunk

    headers = [h.strip() for h in header_line.split("\t")]
    nl_parts = []

    for row_line in lines[1:]:
        if "\t" not in row_line:
            nl_parts.append(row_line)
            continue
        cells = [c.strip() for c in row_line.split("\t")]
        pairs = []
        for h, v in zip(headers, cells):
            if h and v and v not in ("", "X", "-"):
                pairs.append(f"{h}이 {v}")
        if pairs:
            nl_parts.append("이 행은 " + "이고 ".join(pairs) + "입니다.")

    if not nl_parts:
        return chunk
    return header_line + "\n" + "\n".join(nl_parts)
