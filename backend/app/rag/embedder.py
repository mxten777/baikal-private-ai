"""
Embedder - Ollama를 통한 임베딩 생성
"""
from typing import List
from app.services.llm_service import call_ollama_embedding


async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """텍스트 리스트에 대한 임베딩 생성

    배치 처리: 한 번에 처리하되, 에러 시 개별 처리
    """
    if not texts:
        return []

    try:
        embeddings = await call_ollama_embedding(texts)
        return embeddings
    except Exception as e:
        print(f"[EMB] 임베딩 생성 실패: {e}")
        raise
