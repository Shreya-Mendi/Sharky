"""Shared test fixtures for the Shark Tank AI Engine."""

import pytest


SAMPLE_SRT_BRACKET = """1
00:00:00,000 --> 00:00:03,000
[Speaker_1] Welcome to Shark Tank.

2
00:00:03,000 --> 00:00:06,000
[Speaker_1] Tonight, five entrepreneurs will pitch their ideas.

3
00:00:06,000 --> 00:00:10,000
[Speaker_1] First into the tank is Jane Smith, with a revolutionary new product.

4
00:00:10,000 --> 00:00:15,000
[Speaker_2] Hello, my name is Jane Smith from Austin, Texas.

5
00:00:15,000 --> 00:00:20,000
[Speaker_2] I'm asking for $200,000 for 10% of my company, FreshBites.

6
00:00:20,000 --> 00:00:25,000
[Speaker_2] We make healthy snack bars with $500,000 in sales last year.

7
00:00:25,000 --> 00:00:28,000
[Speaker_2] Let me show you how they taste.

8
00:00:28,000 --> 00:00:32,000
[Speaker_3] What's your margin on these?

9
00:00:32,000 --> 00:00:35,000
[Speaker_2] We're at about 40% gross margin.

10
00:00:35,000 --> 00:00:38,000
[Speaker_4] I love this product. How did you get into retail?

11
00:00:38,000 --> 00:00:42,000
[Speaker_2] We started at farmers markets and now we're in 200 stores.

12
00:00:42,000 --> 00:00:45,000
[Speaker_3] The problem is your valuation is too high. I'm out.

13
00:00:45,000 --> 00:00:48,000
[Speaker_5] For that reason, I'm out.

14
00:00:48,000 --> 00:00:52,000
[Speaker_4] I'll offer you $200,000 for 25%.

15
00:00:52,000 --> 00:00:55,000
[Speaker_2] Would you consider 20%?

16
00:00:55,000 --> 00:00:58,000
[Speaker_4] I'll do 22%. Final offer.

17
00:00:58,000 --> 00:01:02,000
[Speaker_2] Deal. Thank you so much.

18
00:01:02,000 --> 00:01:06,000
[Speaker_1] Next up is Bob Lee, who has a tech product the sharks won't believe.

19
00:01:06,000 --> 00:01:10,000
[Speaker_6] Hi, my name is Bob Lee. I'm asking for $1 million for 5%.

20
00:01:10,000 --> 00:01:14,000
[Speaker_6] My company is in the $50 billion dollar market of home automation.

21
00:01:14,000 --> 00:01:17,000
[Speaker_3] What are your sales?

22
00:01:17,000 --> 00:01:20,000
[Speaker_6] We did $100,000 last year.

23
00:01:20,000 --> 00:01:24,000
[Speaker_3] You're crazy. $1 million for a company doing $100K? I'm out.

24
00:01:24,000 --> 00:01:27,000
[Speaker_4] I don't see how this scales. I'm out.

25
00:01:27,000 --> 00:01:30,000
[Speaker_5] Not for me. I'm out.
"""


SAMPLE_SRT_COLON = """1
00:00:00,000 --> 00:00:03,000
Speaker_1: Welcome to Shark Tank.

2
00:00:03,000 --> 00:00:06,000
Speaker_1: Tonight, five entrepreneurs will pitch their ideas.

3
00:00:06,000 --> 00:00:10,000
Speaker_1: First into the tank is Jane Smith, with a revolutionary new product.

4
00:00:10,000 --> 00:00:15,000
Speaker_2: Hello, my name is Jane Smith from Austin, Texas.

5
00:00:15,000 --> 00:00:20,000
Speaker_2: I'm asking for $200,000 for 10% of my company, FreshBites.

6
00:00:20,000 --> 00:00:25,000
Speaker_2: We make healthy snack bars with $500,000 in sales last year.

7
00:00:25,000 --> 00:00:28,000
Speaker_2: Let me show you how they taste.

8
00:00:28,000 --> 00:00:32,000
Speaker_3: What's your margin on these?

9
00:00:32,000 --> 00:00:35,000
Speaker_2: We're at about 40% gross margin.

10
00:00:35,000 --> 00:00:38,000
Speaker_4: I love this product. How did you get into retail?

11
00:00:38,000 --> 00:00:42,000
Speaker_2: We started at farmers markets and now we're in 200 stores.

12
00:00:42,000 --> 00:00:45,000
Speaker_3: The problem is your valuation is too high. I'm out.

13
00:00:45,000 --> 00:00:48,000
Speaker_5: For that reason, I'm out.

14
00:00:48,000 --> 00:00:52,000
Speaker_4: I'll offer you $200,000 for 25%.

15
00:00:52,000 --> 00:00:55,000
Speaker_2: Would you consider 20%?

16
00:00:55,000 --> 00:00:58,000
Speaker_4: I'll do 22%. Final offer.

17
00:00:58,000 --> 00:01:02,000
Speaker_2: Deal. Thank you so much.

18
00:01:02,000 --> 00:01:06,000
Speaker_1: Next up is Bob Lee, who has a tech product the sharks won't believe.

19
00:01:06,000 --> 00:01:10,000
Speaker_6: Hi, my name is Bob Lee. I'm asking for $1 million for 5%.

20
00:01:10,000 --> 00:01:14,000
Speaker_6: My company is in the $50 billion dollar market of home automation.

21
00:01:14,000 --> 00:01:17,000
Speaker_3: What are your sales?

22
00:01:17,000 --> 00:01:20,000
Speaker_6: We did $100,000 last year.

23
00:01:20,000 --> 00:01:24,000
Speaker_3: You're crazy. $1 million for a company doing $100K? I'm out.

24
00:01:24,000 --> 00:01:27,000
Speaker_4: I don't see how this scales. I'm out.

25
00:01:27,000 --> 00:01:30,000
Speaker_5: Not for me. I'm out.
"""


@pytest.fixture
def sample_srt_bracket():
    return SAMPLE_SRT_BRACKET


@pytest.fixture
def sample_srt_colon():
    return SAMPLE_SRT_COLON


@pytest.fixture
def sample_srt_file(tmp_path, sample_srt_bracket):
    srt_file = tmp_path / "S01E01_with_speakers.srt"
    srt_file.write_text(sample_srt_bracket, encoding="utf-8")
    return srt_file


@pytest.fixture
def sample_srt_dir(tmp_path, sample_srt_bracket, sample_srt_colon):
    srt_file1 = tmp_path / "S01E01_with_speakers.srt"
    srt_file1.write_text(sample_srt_bracket, encoding="utf-8")
    srt_file2 = tmp_path / "S03E01.srt"
    srt_file2.write_text(sample_srt_colon, encoding="utf-8")
    return tmp_path
