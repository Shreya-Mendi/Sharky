"""Tests for the embedding pipeline."""

import pytest

from src.embeddings.embed_pipeline import (
    chunk_pitch,
    PitchChunk,
)
from src.ingestion.srt_parser import parse_srt, split_into_pitches, classify_speakers, segment_pitch


class TestChunkPitch:
    """Test pitch chunking into embeddable segments."""

    def test_returns_chunks(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[0], blocks)
        segments = segment_pitch(pitches[0], roles)
        chunks = chunk_pitch(segments, episode="S01E01", pitch_index=0, company_name="FreshBites")
        assert len(chunks) > 0
        assert all(isinstance(c, PitchChunk) for c in chunks)

    def test_chunk_has_metadata(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[0], blocks)
        segments = segment_pitch(pitches[0], roles)
        chunks = chunk_pitch(segments, episode="S01E01", pitch_index=0, company_name="FreshBites")
        chunk = chunks[0]
        assert chunk.episode == "S01E01"
        assert chunk.company_name == "FreshBites"
        assert chunk.segment_type in (
            "founder_pitch", "product_demo", "shark_questions",
            "objections", "negotiation", "closing_reason",
        )

    def test_empty_segments_skipped(self):
        from src.ingestion.srt_parser import PitchSegments
        segments = PitchSegments()  # all empty
        chunks = chunk_pitch(segments, episode="S01E01", pitch_index=0, company_name="Test")
        assert len(chunks) == 0
