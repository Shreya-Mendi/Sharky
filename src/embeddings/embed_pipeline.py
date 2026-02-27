"""embed_pipeline.py — Chunk pitches and embed into Pinecone.

Chunks each pitch by segment type, embeds with OpenAI text-embedding-3-large,
and upserts into Pinecone with metadata for filtered retrieval.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Optional

from src.ingestion.srt_parser import PitchSegments, ParsedPitch


SEGMENT_NAMES = [
    "founder_pitch", "product_demo", "shark_questions",
    "objections", "negotiation", "closing_reason",
]

MAX_CHUNK_TOKENS = 8000
OVERLAP_TOKENS = 200


@dataclass
class PitchChunk:
    """A single embeddable chunk from a pitch segment."""
    text: str
    episode: str
    pitch_index: int
    company_name: str
    segment_type: str
    chunk_index: int = 0


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return len(text) // 4


def _split_text(text: str, max_tokens: int, overlap_tokens: int) -> list[str]:
    """Split text into chunks with overlap if it exceeds max_tokens."""
    if _estimate_tokens(text) <= max_tokens:
        return [text]

    # Split by sentences first
    import re
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for sentence in sentences:
        sent_tokens = _estimate_tokens(sentence)
        if current_tokens + sent_tokens > max_tokens and current:
            chunks.append(" ".join(current))
            # Keep overlap
            overlap_text = " ".join(current)
            overlap_chars = overlap_tokens * 4
            if len(overlap_text) > overlap_chars:
                overlap_start = overlap_text[-overlap_chars:]
                current = [overlap_start]
                current_tokens = overlap_tokens
            else:
                current = list(current)
                current_tokens = _estimate_tokens(" ".join(current))
        current.append(sentence)
        current_tokens += sent_tokens

    if current:
        chunks.append(" ".join(current))

    return chunks if chunks else [text]


def chunk_pitch(
    segments: PitchSegments,
    episode: str,
    pitch_index: int,
    company_name: str,
) -> list[PitchChunk]:
    """Split a pitch's segments into embeddable chunks."""
    chunks: list[PitchChunk] = []

    for seg_name in SEGMENT_NAMES:
        blocks = getattr(segments, seg_name, [])
        if not blocks:
            continue

        full_text = " ".join(b.text for b in blocks)
        if not full_text.strip():
            continue

        text_parts = _split_text(full_text, MAX_CHUNK_TOKENS, OVERLAP_TOKENS)
        for i, part in enumerate(text_parts):
            chunks.append(PitchChunk(
                text=part,
                episode=episode,
                pitch_index=pitch_index,
                company_name=company_name,
                segment_type=seg_name,
                chunk_index=i,
            ))

    return chunks


def embed_chunks(chunks: list[PitchChunk]) -> list[tuple[PitchChunk, list[float]]]:
    """Embed chunks using OpenAI text-embedding-3-large.

    Requires OPENAI_API_KEY in environment.
    Returns list of (chunk, embedding_vector) tuples.
    """
    from openai import OpenAI

    client = OpenAI()
    results: list[tuple[PitchChunk, list[float]]] = []

    # Batch in groups of 100 (OpenAI limit)
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [c.text for c in batch]

        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=texts,
        )

        for chunk, embedding_data in zip(batch, response.data):
            results.append((chunk, embedding_data.embedding))

        # Rate limiting
        if i + batch_size < len(chunks):
            time.sleep(0.5)

    return results


def upsert_to_pinecone(
    embedded_chunks: list[tuple[PitchChunk, list[float]]],
    index_name: Optional[str] = None,
) -> int:
    """Upsert embedded chunks into Pinecone.

    Requires PINECONE_API_KEY in environment.
    Returns count of vectors upserted.
    """
    from pinecone import Pinecone

    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    idx_name = index_name or os.environ.get("PINECONE_INDEX_NAME", "shark-tank-engine")
    index = pc.Index(idx_name)

    vectors = []
    for chunk, embedding in embedded_chunks:
        vector_id = f"{chunk.episode}_p{chunk.pitch_index}_{chunk.segment_type}_c{chunk.chunk_index}"
        metadata = {
            "episode": chunk.episode,
            "pitch_index": chunk.pitch_index,
            "company_name": chunk.company_name,
            "segment_type": chunk.segment_type,
            "text": chunk.text[:1000],  # Pinecone metadata limit
        }
        vectors.append({"id": vector_id, "values": embedding, "metadata": metadata})

    # Batch upsert (Pinecone limit: 100 vectors)
    batch_size = 100
    total = 0
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        index.upsert(vectors=batch)
        total += len(batch)

    return total


def run_pipeline(pitches: list[ParsedPitch]) -> int:
    """Full embedding pipeline: chunk -> embed -> upsert.

    Returns total vectors upserted.
    """
    all_chunks: list[PitchChunk] = []
    for pitch in pitches:
        chunks = chunk_pitch(
            pitch.segments,
            episode=pitch.episode,
            pitch_index=pitch.pitch_index,
            company_name=pitch.entrepreneur_name,
        )
        all_chunks.extend(chunks)

    if not all_chunks:
        return 0

    embedded = embed_chunks(all_chunks)
    return upsert_to_pinecone(embedded)
