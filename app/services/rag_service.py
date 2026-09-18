"""
rag_service.py

Always-on RAG pipeline for the Sakha chat endpoint.

Flow:
  1. Embed the user query locally with all-MiniLM-L6-v2 (singleton, loaded once)
  2. Search the Milvus `ScripturePassages` collection for top-k neighbours
  3. Fetch the full passage rows from Postgres
  4. Return typed RetrievedPassage objects for injection into the LLM prompt
"""

from __future__ import annotations

import os
import asyncio
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List

import psycopg2
from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer

# ── singleton embedding model ─────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    return SentenceTransformer("all-MiniLM-L6-v2")


# ── typed result ─────────────────────────────────────────────────────────────

@dataclass
class RetrievedPassage:
    passage_id: str
    source_name: str
    verse_number: str          # e.g. "2.47"
    translation: str
    sanskrit_text: str | None
    summary: str | None
    score: float               # cosine similarity [0, 1]

    @property
    def reference(self) -> str:
        """Human-readable citation, e.g. 'Bhagavad Gita 2.47'"""
        return f"{self.source_name} {self.verse_number}"

    @property
    def citation_block(self) -> str:
        """Compact text block to inject into the LLM prompt."""
        lines = [
            f"[{self.reference}]",
            f"Translation: {self.translation}",
        ]
        if self.summary:
            lines.append(f"Summary: {self.summary}")
        return "\n".join(lines)


# ── DB config ─────────────────────────────────────────────────────────────────

def _pg_config() -> dict:
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": os.environ.get("DB_PORT", "5432"),
        "dbname": os.environ.get("DB_NAME", "spiritualsakha"),
        "user": os.environ.get("DB_USER", "sakha"),
        "password": os.environ.get("DB_PASSWORD", "sakha_dev_password"),
    }


# ── core search logic (sync — called via run_in_executor) ─────────────────────

def _search_sync(
    query: str,
    top_k: int,
    milvus_host: str,
    milvus_port: int,
) -> List[RetrievedPassage]:
    model = _get_model()
    query_vector = model.encode(query).tolist()

    # ── Milvus search ────────────────────────────────────────────────────────
    client = MilvusClient(uri=f"http://{milvus_host}:{milvus_port}")
    results = client.search(
        collection_name="ScripturePassages",
        data=[query_vector],
        limit=top_k,
        output_fields=["passage_id", "source_name"],
        search_params={"metric_type": "COSINE", "params": {"ef": 64}},
    )

    if not results or not results[0]:
        return []

    hits = results[0]  # single query → first (and only) result list
    passage_ids = [h["entity"]["passage_id"] for h in hits]
    score_map = {h["entity"]["passage_id"]: h["distance"] for h in hits}

    if not passage_ids:
        return []

    # ── Postgres fetch ───────────────────────────────────────────────────────
    conn = psycopg2.connect(**_pg_config())
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT p.id, s.name, p.verse_number,
                       p.translation, p.sanskrit_text, p.summary
                FROM passages p
                JOIN sources s ON p.source_id = s.id
                WHERE p.id = ANY(%s::uuid[])
                """,
                (passage_ids,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    passages: List[RetrievedPassage] = []
    for row in rows:
        pid = str(row[0])
        passages.append(
            RetrievedPassage(
                passage_id=pid,
                source_name=row[1],
                verse_number=row[2] or "",
                translation=row[3],
                sanskrit_text=row[4],
                summary=row[5],
                score=score_map.get(pid, 0.0),
            )
        )

    # Sort by cosine similarity descending
    passages.sort(key=lambda p: p.score, reverse=True)
    return passages


# ── async public API ──────────────────────────────────────────────────────────

class RagService:
    def __init__(self, milvus_host: str = "localhost", milvus_port: int = 19530):
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port

    async def search(self, query: str, top_k: int = 5) -> List[RetrievedPassage]:
        """
        Non-blocking RAG search. Runs the CPU-bound embedding + Postgres IO
        in a thread-pool executor so the FastAPI event loop stays free.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            _search_sync,
            query,
            top_k,
            self.milvus_host,
            self.milvus_port,
        )
