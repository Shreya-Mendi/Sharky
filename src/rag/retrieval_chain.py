"""retrieval_chain.py — RAG pipeline over Shark Tank pitch data.

Retrieves relevant pitch segments using local sentence-transformer embeddings
(all-MiniLM-L6-v2) with cross-encoder reranking, then synthesises analysis
via Claude. No external vector database required — the corpus is small enough
(~741 pitches) to retrieve in-process.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from src.data.cache import get_all_pitches, classify_industry
from src.nlp.hybrid_ai import semantic_retrieve

SYSTEM_PROMPT = """You are a venture pitch analyst with deep expertise in startup evaluation,
deal negotiation patterns, and investor psychology. You have access to a database of
real pitch transcripts, deal outcomes, and market data from a multi-season pitch corpus.

When answering questions:
- Ground your analysis in specific data from retrieved pitches
- Cite episode codes and company names
- Provide quantitative evidence (deal amounts, success rates, margins)
- Identify patterns across multiple pitches when relevant
- Give actionable insights for founders or investors

Format your response with clear sections and bullet points when appropriate."""


@dataclass
class SourceCitation:
    """A citation reference from the RAG response."""
    episode: str
    company_name: str
    segment_type: str
    text_snippet: str


@dataclass
class AnalysisResult:
    """Result from the RAG analysis pipeline."""
    answer: str
    sources: list[SourceCitation]
    query: str


def _build_corpus_docs() -> list[dict]:
    """Build flat document list from cached pitches for embedding retrieval."""
    pitches = get_all_pitches()
    docs = []
    for pitch in pitches:
        segs = pitch.get("segments", {})
        for seg_name, blocks in segs.items():
            if not isinstance(blocks, list) or not blocks:
                continue
            text = " ".join(blocks)
            if len(text.strip()) < 30:
                continue
            docs.append({
                "text": text[:1500],
                "episode": pitch.get("episode", ""),
                "company_name": pitch.get("entrepreneur_name", "Unknown"),
                "segment_type": seg_name,
                "industry": classify_industry(pitch),
            })
    return docs


def retrieve_context(
    query: str,
    top_k: int = 5,
    filters: Optional[dict] = None,
) -> list[dict]:
    """Retrieve relevant pitch segments using local embedding + reranking.

    Uses sentence-transformers/all-MiniLM-L6-v2 for dense retrieval and
    cross-encoder/ms-marco-MiniLM-L-6-v2 for reranking when available.
    Falls back to lexical overlap scoring if no GPU/models present.
    """
    docs = _build_corpus_docs()

    if filters and filters.get("industry"):
        target = filters["industry"].lower()
        docs = [d for d in docs if target in d.get("industry", "").lower()]

    hits = semantic_retrieve(query, docs, text_key="text", top_k=top_k)
    results = []
    for idx, score in hits:
        doc = docs[idx]
        results.append({
            "text": doc["text"],
            "episode": doc["episode"],
            "company_name": doc["company_name"],
            "segment_type": doc["segment_type"],
            "score": round(float(score), 4),
        })
    return results


def build_analysis_prompt(query: str, context_docs: list[dict]) -> str:
    """Build the full prompt with system prompt, context, and query."""
    context_parts: list[str] = []
    for doc in context_docs:
        episode = doc.get("episode", "Unknown")
        company = doc.get("company_name", "Unknown")
        segment = doc.get("segment_type", "")
        text = doc.get("text", "")
        context_parts.append(f"[{episode} - {company} ({segment})]\n{text}")

    context_str = "\n\n".join(context_parts) if context_parts else "No relevant context found."

    return f"""{SYSTEM_PROMPT}

## Retrieved Context

{context_str}

## User Query

{query}

## Instructions

Answer the user's query using the retrieved context above. Cite specific episodes and companies.
If the context doesn't contain relevant information, say so and provide general insights."""


def analyze(
    query: str,
    top_k: int = 5,
    filters: Optional[dict] = None,
) -> AnalysisResult:
    """Full RAG pipeline: retrieve -> prompt -> synthesise via Claude."""
    import anthropic

    context_docs = retrieve_context(query, top_k=top_k, filters=filters)
    prompt = build_analysis_prompt(query, context_docs)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    answer = message.content[0].text
    sources = [
        SourceCitation(
            episode=doc.get("episode", ""),
            company_name=doc.get("company_name", ""),
            segment_type=doc.get("segment_type", ""),
            text_snippet=doc.get("text", "")[:200],
        )
        for doc in context_docs
    ]
    return AnalysisResult(answer=answer, sources=sources, query=query)


def analyze_stream(
    query: str,
    top_k: int = 5,
    filters: Optional[dict] = None,
):
    """Streaming RAG pipeline. Yields chunks of Claude's response."""
    import anthropic

    context_docs = retrieve_context(query, top_k=top_k, filters=filters)
    prompt = build_analysis_prompt(query, context_docs)

    sources = [
        {
            "episode": doc.get("episode", ""),
            "company_name": doc.get("company_name", ""),
            "segment_type": doc.get("segment_type", ""),
            "text_snippet": doc.get("text", "")[:200],
        }
        for doc in context_docs
    ]
    yield {"type": "sources", "data": sources}

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)
    with client.messages.stream(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            yield {"type": "text", "data": text}
