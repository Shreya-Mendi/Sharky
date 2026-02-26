"""Tests for the SRT parser module."""

from src.ingestion.srt_parser import (
    SubtitleBlock,
    parse_srt,
    parse_srt_file,
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
