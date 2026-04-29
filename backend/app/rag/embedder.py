"""
Embedder - Ollama를 통한 임베딩 생성
"""
import logging
from typing import List
from app.services.llm_service import call_ollama_embedding

logger = logging.getLogger("baikal.embedder")


async def generate_embeddings(texts: List[str], progress_cb=None) -> List[List[float]]:
    """텍스트 리스트에 대한 임베딩 생성

    Stage 1.2b: 실제 batch 호출로 변경 (Ollama `/api/embed` input=list).
    progress_cb(done, total): 매 batch 완료 시 호출.
    """
    if not texts:
        return []

    try:
        embeddings = await call_ollama_embedding(texts, progress_cb=progress_cb)
        return embeddings
    except Exception as e:
        logger.error(f"임베딩 생성 실패: {e}")
        raise
