"""Integration tests for the analyze_video worker task (M2-4).

These tests exercise the parsing and segment generation logic
without a real database or Celery broker.
"""
import os
import tempfile
import uuid

import pytest
from unittest.mock import MagicMock, patch

from worker.tasks.video_processing import (
    _generate_segments_from_cues,
    _ms,
    parse_srt,
    parse_vtt,
)

# ── Unit tests for helpers ──────────────────────────────────────────────────

class TestMsConverter:
    def test_basic_vtt(self):
        assert _ms("00:01:00.000") == 60_000

    def test_with_comma(self):
        assert _ms("00:00:01,500") == 1_500

    def test_hours(self):
        assert _ms("01:30:00.000") == 5_400_000


class TestParseVtt:
    VTT_CONTENT = """\
WEBVTT

00:00:00.000 --> 00:00:04.000
안녕하세요

00:00:04.000 --> 00:00:08.000
오늘은 분수를 배웁니다
"""

    def test_parses_two_cues(self):
        cues = parse_vtt(self.VTT_CONTENT)
        assert len(cues) == 2
        assert cues[0]["seq_no"] == 1
        assert cues[0]["start_ms"] == 0
        assert cues[0]["end_ms"] == 4_000
        assert cues[0]["text"] == "안녕하세요"

    def test_second_cue(self):
        cues = parse_vtt(self.VTT_CONTENT)
        assert cues[1]["start_ms"] == 4_000
        assert cues[1]["end_ms"] == 8_000


class TestParseSrt:
    SRT_CONTENT = """\
1
00:00:00,000 --> 00:00:04,000
First line

2
00:00:04,000 --> 00:00:08,000
Second line
"""

    def test_parses_two_cues(self):
        cues = parse_srt(self.SRT_CONTENT)
        assert len(cues) == 2
        assert cues[0]["seq_no"] == 1
        assert cues[0]["text"] == "First line"
        assert cues[1]["text"] == "Second line"


class TestGenerateSegments:
    def _make_cues(self, count: int, duration_ms: int = 60_000) -> list[dict]:
        return [
            {
                "seq_no": i + 1,
                "start_ms": i * duration_ms,
                "end_ms": (i + 1) * duration_ms,
                "text": f"Cue {i+1}",
            }
            for i in range(count)
        ]

    def test_empty_cues(self):
        assert _generate_segments_from_cues([]) == []

    def test_single_short_cue_becomes_one_segment(self):
        cues = self._make_cues(1, 30_000)
        segs = _generate_segments_from_cues(cues)
        assert len(segs) == 1
        assert segs[0]["seq_no"] == 1
        assert segs[0]["start_ms"] == 0
        assert segs[0]["end_ms"] == 30_000

    def test_long_video_splits_into_multiple_segments(self):
        # 10 cues × 1 min = 10 min → should create 2 segments (5 min each)
        cues = self._make_cues(10, 60_000)
        segs = _generate_segments_from_cues(cues)
        assert len(segs) >= 2


# ── Integration test: analyze_video task logic ──────────────────────────────

class TestAnalyzeVideoTask:
    VTT = """\
WEBVTT

00:00:00.000 --> 00:05:00.000
First block

00:05:00.000 --> 00:10:00.000
Second block
"""

    def _setup_db_mocks(self, db_session, video_mock, subtitle_path):
        """Wire up mocks to simulate DB state."""
        from models.core import VideoStatus
        video_mock.status = VideoStatus.uploaded
        video_mock.analyzed_at = None

        asset_mock = MagicMock()
        asset_mock.storage_path = subtitle_path
        asset_mock.asset_type = "subtitle_file"

        def scalar_side_effect(stmt):
            from models.core import Video
            from models.video import VideoAsset
            from models.segment import SegmentSet
            stmt_str = str(stmt)
            if "videos" in stmt_str:
                return video_mock
            if "video_assets" in stmt_str:
                return asset_mock
            if "segment_sets" in stmt_str:
                return None
            return None

        db_session.scalar = MagicMock(side_effect=scalar_side_effect)
        db_session.add = MagicMock()
        db_session.flush = MagicMock()
        db_session.commit = MagicMock()
        db_session.close = MagicMock()
        return db_session

    def test_analyze_creates_segment_set(self):
        with tempfile.NamedTemporaryFile(suffix=".vtt", mode="w", delete=False, encoding="utf-8") as f:
            f.write(self.VTT)
            vtt_path = f.name

        try:
            video_id = str(uuid.uuid4())
            db_mock = MagicMock()
            video_mock = MagicMock()

            from models.core import VideoStatus
            video_mock.status = VideoStatus.uploaded
            video_mock.analyzed_at = None

            asset_mock = MagicMock()
            asset_mock.storage_path = vtt_path
            asset_mock.asset_type = "subtitle_file"

            call_count = [0]

            def scalar_side(stmt):
                call_count[0] += 1
                s = str(stmt)
                if "video_assets" in s:
                    return asset_mock
                if "segment_sets" in s:
                    return None
                return video_mock

            db_mock.scalar = MagicMock(side_effect=scalar_side)
            db_mock.add = MagicMock()
            db_mock.flush = MagicMock()
            db_mock.commit = MagicMock()
            db_mock.close = MagicMock()

            with patch("worker.tasks.video_processing._get_db_session", return_value=db_mock):
                from worker.tasks.video_processing import analyze_video
                # Call the underlying function directly (bypass Celery)
                result = analyze_video.__wrapped__(None, video_id)

            assert result["status"] == "success"
            assert result["segment_count"] >= 1
            assert video_mock.status.value == "analyzed" or str(video_mock.status) in ("analyzed", "VideoStatus.analyzed")

        finally:
            os.unlink(vtt_path)

    def test_analyze_fails_gracefully_when_no_subtitle(self):
        video_id = str(uuid.uuid4())
        db_mock = MagicMock()
        video_mock = MagicMock()

        from models.core import VideoStatus
        video_mock.status = VideoStatus.uploaded

        def scalar_side(stmt):
            s = str(stmt)
            if "video_assets" in s:
                return None
            if "segment_sets" in s:
                return None
            return video_mock

        db_mock.scalar = MagicMock(side_effect=scalar_side)
        db_mock.add = MagicMock()
        db_mock.flush = MagicMock()
        db_mock.commit = MagicMock()
        db_mock.close = MagicMock()

        with patch("worker.tasks.video_processing._get_db_session", return_value=db_mock):
            from worker.tasks.video_processing import analyze_video
            result = analyze_video.__wrapped__(None, video_id)

        assert result["status"] == "failed"
        assert result["reason"] == "no_subtitle"
