"""Tests for the SRT parser module."""

from src.ingestion.srt_parser import (
    SubtitleBlock,
    parse_srt,
    parse_srt_file,
    split_into_pitches,
    classify_speakers,
    segment_pitch,
    extract_signals,
    parse_episode,
    parse_all_episodes,
    ParsedPitch,
)


class TestParseSrt:
    """Test raw SRT text parsing."""

    def test_parse_bracket_format(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        assert len(blocks) == 25
        assert blocks[0].index == 1
        assert blocks[0].start_seconds == 0.0
        assert blocks[0].end_seconds == 3.0
        assert blocks[0].speaker == "Speaker_1"
        assert blocks[0].text == "Welcome to Shark Tank."

    def test_parse_colon_format(self, sample_srt_colon):
        blocks = parse_srt(sample_srt_colon)
        assert len(blocks) == 25
        assert blocks[0].speaker == "Speaker_1"
        assert blocks[0].text == "Welcome to Shark Tank."

    def test_speaker_extracted_from_brackets(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        assert blocks[3].speaker == "Speaker_2"
        assert "Jane Smith" in blocks[3].text

    def test_speaker_extracted_from_colon(self, sample_srt_colon):
        blocks = parse_srt(sample_srt_colon)
        assert blocks[3].speaker == "Speaker_2"
        assert "Jane Smith" in blocks[3].text

    def test_timestamps_parsed_correctly(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        assert blocks[2].start_seconds == 6.0
        assert blocks[2].end_seconds == 10.0
        assert blocks[17].start_seconds == 62.0
        assert blocks[17].end_seconds == 66.0

    def test_html_tags_stripped(self):
        srt = """1
00:00:00,000 --> 00:00:03,000
[Speaker_1] <i>Welcome</i> to <b>Shark Tank</b>.
"""
        blocks = parse_srt(srt)
        assert blocks[0].text == "Welcome to Shark Tank."

    def test_empty_input(self):
        blocks = parse_srt("")
        assert blocks == []

    def test_malformed_blocks_skipped(self):
        srt = """not a number
00:00:00,000 --> 00:00:03,000
[Speaker_1] This should be skipped.

2
bad timestamp
[Speaker_1] This too.

3
00:00:06,000 --> 00:00:10,000
[Speaker_1] This one is valid.
"""
        blocks = parse_srt(srt)
        assert len(blocks) == 1
        assert blocks[0].text == "This one is valid."


class TestParseSrtFile:
    """Test SRT file reading."""

    def test_read_file(self, sample_srt_file):
        blocks = parse_srt_file(sample_srt_file)
        assert len(blocks) == 25

    def test_file_not_found(self, tmp_path):
        import pytest
        with pytest.raises(FileNotFoundError):
            parse_srt_file(tmp_path / "nonexistent.srt")


class TestSplitIntoPitches:
    def test_two_pitches_bracket_format(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        assert len(pitches) == 2

    def test_two_pitches_colon_format(self, sample_srt_colon):
        blocks = parse_srt(sample_srt_colon)
        pitches = split_into_pitches(blocks)
        assert len(pitches) == 2

    def test_first_pitch_contains_jane(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        first_pitch_text = " ".join(b.text for b in pitches[0])
        assert "Jane Smith" in first_pitch_text

    def test_second_pitch_contains_bob(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        second_pitch_text = " ".join(b.text for b in pitches[1])
        assert "Bob Lee" in second_pitch_text

    def test_intro_blocks_excluded_from_pitches(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        first_block = pitches[0][0]
        assert "First into the tank" in first_block.text or "Jane" in first_block.text

    def test_single_pitch_no_boundary(self):
        srt = """1
00:00:00,000 --> 00:00:05,000
[Speaker_1] Hello, my name is Alice. I'm asking for $100,000 for 10%.

2
00:00:05,000 --> 00:00:10,000
[Speaker_2] What are your sales?
"""
        blocks = parse_srt(srt)
        pitches = split_into_pitches(blocks)
        assert len(pitches) == 1

    def test_empty_input(self):
        pitches = split_into_pitches([])
        assert pitches == []


class TestClassifySpeakers:
    def test_narrator_identified(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, confidences = classify_speakers(pitches[0], blocks)
        assert roles["Speaker_1"] == "narrator"

    def test_entrepreneur_identified(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, confidences = classify_speakers(pitches[0], blocks)
        assert roles["Speaker_2"] == "entrepreneur"

    def test_sharks_identified(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, confidences = classify_speakers(pitches[0], blocks)
        shark_speakers = [s for s, r in roles.items() if r == "shark"]
        assert len(shark_speakers) >= 2

    def test_confidence_scores_between_0_and_1(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, confidences = classify_speakers(pitches[0], blocks)
        for speaker, score in confidences.items():
            assert 0.0 <= score <= 1.0

    def test_second_pitch_different_entrepreneur(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles1, _ = classify_speakers(pitches[0], blocks)
        roles2, _ = classify_speakers(pitches[1], blocks)
        entrepreneurs1 = [s for s, r in roles1.items() if r == "entrepreneur"]
        entrepreneurs2 = [s for s, r in roles2.items() if r == "entrepreneur"]
        assert entrepreneurs1 != entrepreneurs2


class TestSegmentPitch:
    def test_founder_pitch_captured(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[0], blocks)
        segments = segment_pitch(pitches[0], roles)
        assert len(segments.founder_pitch) > 0
        texts = [b.text for b in segments.founder_pitch]
        assert any("asking for" in t for t in texts)

    def test_product_demo_captured(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[0], blocks)
        segments = segment_pitch(pitches[0], roles)
        demo_texts = [b.text for b in segments.product_demo]
        assert any("show" in t.lower() for t in demo_texts)

    def test_objections_captured(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[0], blocks)
        segments = segment_pitch(pitches[0], roles)
        assert len(segments.objections) >= 2
        obj_texts = [b.text for b in segments.objections]
        assert any("I'm out" in t for t in obj_texts)

    def test_negotiation_captured(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[0], blocks)
        segments = segment_pitch(pitches[0], roles)
        assert len(segments.negotiation) >= 1

    def test_shark_questions_captured(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[0], blocks)
        segments = segment_pitch(pitches[0], roles)
        assert len(segments.shark_questions) >= 1
        q_texts = [b.text for b in segments.shark_questions]
        assert any("?" in t for t in q_texts)


class TestExtractSignals:
    def test_revenue_extracted(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[0], blocks)
        segments = segment_pitch(pitches[0], roles)
        signals = extract_signals(pitches[0], segments, roles)
        assert signals.revenue_mentioned == 500_000.0

    def test_objection_count(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[0], blocks)
        segments = segment_pitch(pitches[0], roles)
        signals = extract_signals(pitches[0], segments, roles)
        assert signals.objection_count >= 2

    def test_negotiation_rounds(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[0], blocks)
        segments = segment_pitch(pitches[0], roles)
        signals = extract_signals(pitches[0], segments, roles)
        assert signals.negotiation_rounds >= 1

    def test_founder_confidence_is_float(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[0], blocks)
        segments = segment_pitch(pitches[0], roles)
        signals = extract_signals(pitches[0], segments, roles)
        assert isinstance(signals.founder_confidence, float)
        assert -1.0 <= signals.founder_confidence <= 1.0

    def test_market_size_from_second_pitch(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[1], blocks)
        segments = segment_pitch(pitches[1], roles)
        signals = extract_signals(pitches[1], segments, roles)
        assert signals.market_size_claim == 50_000_000_000.0


class TestParseEpisode:
    """Test full episode parsing pipeline."""

    def test_returns_parsed_pitches(self, sample_srt_file):
        pitches = parse_episode(sample_srt_file)
        assert len(pitches) == 2
        assert all(isinstance(p, ParsedPitch) for p in pitches)

    def test_episode_code_extracted(self, sample_srt_file):
        pitches = parse_episode(sample_srt_file)
        assert pitches[0].episode == "S01E01"

    def test_entrepreneur_name_extracted(self, sample_srt_file):
        pitches = parse_episode(sample_srt_file)
        assert "Jane Smith" in pitches[0].entrepreneur_name

    def test_pitch_index_sequential(self, sample_srt_file):
        pitches = parse_episode(sample_srt_file)
        assert pitches[0].pitch_index == 0
        assert pitches[1].pitch_index == 1

    def test_signals_populated(self, sample_srt_file):
        pitches = parse_episode(sample_srt_file)
        assert pitches[0].signals.revenue_mentioned > 0
        assert pitches[0].signals.objection_count >= 2

    def test_to_dict_serializable(self, sample_srt_file):
        import json
        pitches = parse_episode(sample_srt_file)
        # Should not raise
        json.dumps(pitches[0].to_dict())


class TestParseAllEpisodes:
    """Test batch episode parsing."""

    def test_parses_multiple_files(self, sample_srt_dir):
        pitches = parse_all_episodes(sample_srt_dir)
        # 2 files * 2 pitches each = 4 total
        assert len(pitches) == 4

    def test_empty_directory(self, tmp_path):
        import pytest
        with pytest.raises(FileNotFoundError):
            parse_all_episodes(tmp_path)
