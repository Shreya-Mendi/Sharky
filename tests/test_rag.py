"""Tests for the RAG retrieval chain (unit tests with mocks)."""

import pytest

from src.rag.retrieval_chain import (
    build_analysis_prompt,
    SYSTEM_PROMPT,
)


class TestBuildPrompt:
    def test_includes_system_prompt(self):
        prompt = build_analysis_prompt("What are the best food pitches?", [])
        assert SYSTEM_PROMPT in prompt

    def test_includes_user_query(self):
        prompt = build_analysis_prompt("What are the best food pitches?", [])
        assert "What are the best food pitches?" in prompt

    def test_includes_context(self):
        context = [
            {"text": "FreshBites had $500K revenue", "episode": "S01E01"},
        ]
        prompt = build_analysis_prompt("Tell me about food startups", context)
        assert "FreshBites" in prompt
        assert "S01E01" in prompt
