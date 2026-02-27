"""retrieval_chain.py — RAG pipeline over Shark Tank pitch data.

Retrieves relevant pitch segments from Pinecone, augments with
structured data from PostgreSQL, and synthesises analysis via Claude.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

SYSTEM_PROMPT = """You are a Shark Tank market analyst with deep expertise in startup evaluation,
deal negotiation patterns, and investor psychology. You have access to a comprehensive
database of every Shark Tank pitch, including transcripts, deal outcomes, and market data.

When answering questions:
- Ground your analysis in specific data from retrieved pitches
- Cite episode numbers and company names
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


def build_analysis_prompt(query: str, context_docs: list[dict]) -> str:
    """Build the full prompt with system prompt, context, and query."""
    context_parts: list[str] = []
    for doc in context_docs:
        episode = doc.get("episode", "Unknown")
        company = doc.get("company_name", "Unknown")
        segment = doc.get("segment_type", "")
        text = doc.get("text", "")
        context_parts.append(
            f"[{episode} - {company} ({segment})]\n{text}"
        )

    context_str = "\n\n".join(context_parts) if context_parts else "No relevant context found."

    return f"""{SYSTEM_PROMPT}

## Retrieved Context

{context_str}

## User Query

{query}

## Instructions

Answer the user's query using the retrieved context above. Cite specific episodes and companies.
If the context doesn't contain relevant information, say so and provide general insights."""


def retrieve_context(
    query: str,
    top_k: int = 5,
    filters: Optional[dict] = None,
) -> list[dict]:
    """Retrieve relevant pitch segments from Pinecone.

    Requires OPENAI_API_KEY and PINECONE_API_KEY in environment.
    """
    from openai import OpenAI
    from pinecone import Pinecone

    # Embed query
    openai_client = OpenAI()
    response = openai_client.embeddings.create(
        model="text-embedding-3-large",
        input=[query],
    )
    query_embedding = response.data[0].embedding

    # Search Pinecone
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    index_name = os.environ.get("PINECONE_INDEX_NAME", "shark-tank-engine")
    index = pc.Index(index_name)

    query_params = {
        "vector": query_embedding,
        "top_k": top_k,
        "include_metadata": True,
    }
    if filters:
        query_params["filter"] = filters

    results = index.query(**query_params)

    context_docs = []
    for match in results.get("matches", []):
        metadata = match.get("metadata", {})
        context_docs.append({
            "text": metadata.get("text", ""),
            "episode": metadata.get("episode", ""),
            "company_name": metadata.get("company_name", ""),
            "segment_type": metadata.get("segment_type", ""),
            "score": match.get("score", 0.0),
        })

    return context_docs


def analyze(
    query: str,
    top_k: int = 5,
    filters: Optional[dict] = None,
) -> AnalysisResult:
    """Full RAG pipeline: retrieve -> prompt -> synthesise.

    Requires ANTHROPIC_API_KEY, OPENAI_API_KEY, and PINECONE_API_KEY.
    """
    import anthropic

    # Retrieve context
    context_docs = retrieve_context(query, top_k=top_k, filters=filters)

    # Build prompt
    prompt = build_analysis_prompt(query, context_docs)

    # Call Claude
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    answer = message.content[0].text

    # Build citations
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
