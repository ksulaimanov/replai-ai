import os
import chromadb
from dotenv import load_dotenv

load_dotenv()

_client = chromadb.CloudClient(
    api_key=os.getenv("CHROMA_API_KEY"),
    tenant=os.getenv("CHROMA_TENANT"),
    database=os.getenv("CHROMA_DATABASE"),
)

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def _split(text: str) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start : start + CHUNK_SIZE])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def _collection(bot_id: str):
    return _client.get_or_create_collection(bot_id)


def add_to_knowledge_base(bot_id: str, text: str) -> None:
    chunks = _split(text)
    col = _collection(bot_id)
    existing = col.count()
    col.add(
        documents=chunks,
        ids=[f"chunk_{existing + i}" for i in range(len(chunks))],
    )


def search_knowledge_base(bot_id: str, query: str) -> str:
    try:
        col = _client.get_collection(bot_id)
    except Exception:
        return ""
    if col.count() == 0:
        return ""
    results = col.query(query_texts=[query], n_results=min(3, col.count()))
    docs = results.get("documents", [[]])[0]
    return "\n\n".join(docs)


def delete_knowledge_base(bot_id: str) -> None:
    try:
        _client.delete_collection(bot_id)
    except Exception:
        pass
