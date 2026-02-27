"""
Retriever - Vector 검색
"""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text as sql_text
from app.services.llm_service import call_ollama_embedding
from app.config import get_settings

settings = get_settings()


async def retrieve_relevant_chunks(
    query: str, db: AsyncSession, top_k: int = None
) -> List[dict]:
    """질문과 관련된 문서 청크 검색"""
    if top_k is None:
        top_k = settings.TOP_K

    # 질문 임베딩
    embeddings = await call_ollama_embedding([query])
    query_embedding = embeddings[0]

    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    # pgvector cosine distance 검색
    search_query = sql_text("""
        SELECT dc.id, dc.content, dc.document_id, dc.chunk_index,
               d.filename,
               dc.embedding <=> :embedding::vector AS distance
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE d.status = 'completed'
        ORDER BY dc.embedding <=> :embedding::vector
        LIMIT :top_k
    """)

    result = await db.execute(
        search_query,
        {"embedding": embedding_str, "top_k": top_k},
    )
    rows = result.fetchall()

    results = []
    for row in rows:
        chunk_id, content, doc_id, chunk_index, filename, distance = row
        results.append({
            "chunk_id": chunk_id,
            "content": content,
            "document_id": doc_id,
            "chunk_index": chunk_index,
            "filename": filename,
            "score": round(1 - distance, 4),
        })

    return results
