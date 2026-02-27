"""
LLM Service - Ollama API 호출
"""
import logging
import json
import asyncio
import httpx
from typing import List, AsyncGenerator
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger("baikal.llm")


class OllamaConnectionError(Exception):
    """Ollama 서버 연결 실패"""
    pass


class OllamaModelError(Exception):
    """Ollama 모델 오류"""
    pass


async def _ollama_request(method: str, path: str, **kwargs) -> httpx.Response:
    """Ollama API 요청 (공통 에러 처리)"""
    url = f"{settings.OLLAMA_BASE_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=kwargs.pop("timeout", 300.0)) as client:
            response = await getattr(client, method)(url, **kwargs)
            response.raise_for_status()
            return response
    except httpx.ConnectError:
        logger.error(f"Ollama 서버 연결 실패: {settings.OLLAMA_BASE_URL}")
        raise OllamaConnectionError(
            f"Ollama 서버에 연결할 수 없습니다 ({settings.OLLAMA_BASE_URL}). "
            "Ollama가 실행 중인지 확인하세요."
        )
    except httpx.TimeoutException:
        logger.error(f"Ollama 요청 타임아웃: {path}")
        raise OllamaConnectionError("Ollama 서버 응답 시간 초과. LLM 모델 로딩에 시간이 걸릴 수 있습니다.")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise OllamaModelError(
                f"모델을 찾을 수 없습니다. 'ollama pull {settings.LLM_MODEL}' 명령으로 모델을 다운로드하세요."
            )
        logger.error(f"Ollama HTTP 에러: {e.response.status_code} - {e.response.text}")
        raise


async def call_ollama_chat(prompt: str = "", system_prompt: str = "", messages: list = None) -> str:
    """Ollama Chat API 호출"""
    if messages is None:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

    response = await _ollama_request(
        "post",
        "/api/chat",
        json={
            "model": settings.LLM_MODEL,
            "messages": messages,
            "stream": False,
        },
        timeout=300.0,
    )
    data = response.json()
    return data["message"]["content"]


async def call_ollama_chat_stream(prompt: str = "", system_prompt: str = "", messages: list = None) -> AsyncGenerator[str, None]:
    """Ollama Chat API 스트리밍 호출"""
    if messages is None:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

    url = f"{settings.OLLAMA_BASE_URL}/api/chat"
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                url,
                json={
                    "model": settings.LLM_MODEL,
                    "messages": messages,
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()
                import json as _json
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = _json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
    except httpx.ConnectError:
        raise OllamaConnectionError("Ollama 서버에 연결할 수 없습니다.")
    except httpx.TimeoutException:
        raise OllamaConnectionError("Ollama 서버 응답 시간 초과.")


async def call_ollama_embedding(texts: List[str]) -> List[List[float]]:
    """Ollama Embedding API 호출 (배치 처리 + 재시도)"""
    embeddings = []
    batch_size = 10  # 한 번에 처리할 텍스트 수

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        for text in batch:
            retry_count = 0
            max_retries = 3

            while retry_count < max_retries:
                try:
                    response = await _ollama_request(
                        "post",
                        "/api/embed",
                        json={
                            "model": settings.EMBEDDING_MODEL,
                            "input": text,
                        },
                        timeout=120.0,
                    )
                    data = response.json()
                    embeddings.append(data["embeddings"][0])
                    break
                except (OllamaConnectionError, OllamaModelError):
                    raise
                except Exception as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error(f"임베딩 생성 실패 (최대 재시도 초과): {e}")
                        raise
                    logger.warning(f"임베딩 재시도 {retry_count}/{max_retries}: {e}")
                    await asyncio.sleep(1)

    return embeddings


async def check_ollama_health() -> bool:
    """Ollama 서버 상태 확인"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            return response.status_code == 200
    except Exception:
        return False


async def list_ollama_models() -> list:
    """설치된 Ollama 모델 목록"""
    try:
        response = await _ollama_request("get", "/api/tags", timeout=10.0)
        data = response.json()
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []
