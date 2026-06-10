"""Tests for metrics aggregation worker (M3-6, M3-7).

Pure-function tests for risk flag / stability / per-segment aggregation logic.
Heavy DB integration is covered by the contract test for the funnel API.
"""
import uuid
from types import SimpleNamespace

import pytest

from worker.tasks.metrics_aggregation import (
    DROPOUT_SPIKE_THRESHOLD,
    LOW_EXPLICIT_SIGNAL_THRESHOLD,
    MIN_VIEWERS_FOR_FLAGS,
    REWATCH_SPIKE_THRESHOLD,
    TRANSITION_DROP_THRESHOLD,
    _aggregate_segment_metrics,
    compute_risk_flags,
    compute_stability_score,
)


def _evt(event_type: str, session_id, value=None):
    return SimpleNamespace(
        event_type=SimpleNamespace(value=event_type),
        learner_session_id=session_id,
        event_value=value,
    )


class TestRiskFlags:
    BASE_METRICS = {
        "completion_rate": 0.8,
        "dropout_rate": 0.2,
        "rewatch_rate": 0.1,
        "next_transition_rate": 0.9,
        "explicit_response_rate": 0.5,
    }

    def test_no_flags_below_min_viewers(self):
        metrics = {**self.BASE_METRICS, "dropout_rate": 0.9}
        assert compute_risk_flags(metrics, viewers_started=MIN_VIEWERS_FOR_FLAGS - 1) == []

    def test_dropout_spike_flag(self):
        metrics = {**self.BASE_METRICS, "dropout_rate": DROPOUT_SPIKE_THRESHOLD}
        flags = compute_risk_flags(metrics, viewers_started=MIN_VIEWERS_FOR_FLAGS)
        assert "dropout_spike" in flags

    def test_rewatch_spike_flag(self):
        metrics = {**self.BASE_METRICS, "rewatch_rate": REWATCH_SPIKE_THRESHOLD}
        flags = compute_risk_flags(metrics, viewers_started=MIN_VIEWERS_FOR_FLAGS)
        assert "rewatch_spike" in flags

    def test_low_explicit_signal_flag(self):
        metrics = {
            **self.BASE_METRICS,
            "explicit_response_rate": LOW_EXPLICIT_SIGNAL_THRESHOLD - 0.01,
        }
        flags = compute_risk_flags(metrics, viewers_started=MIN_VIEWERS_FOR_FLAGS)
        assert "low_explicit_signal" in flags

    def test_transition_drop_flag(self):
        metrics = {
            **self.BASE_METRICS,
            "next_transition_rate": TRANSITION_DROP_THRESHOLD - 0.01,
        }
        flags = compute_risk_flags(metrics, viewers_started=MIN_VIEWERS_FOR_FLAGS)
        assert "transition_drop" in flags

    def test_no_flags_when_healthy(self):
        assert compute_risk_flags(self.BASE_METRICS, viewers_started=200) == []


class TestStabilityScore:
    def test_perfect_signals(self):
        metrics = {
            "completion_rate": 1.0,
            "next_transition_rate": 1.0,
            "confidence_positive_rate": 1.0,
        }
        assert compute_stability_score(metrics) == 1.0

    def test_zero_signals(self):
        metrics = {
            "completion_rate": 0.0,
            "next_transition_rate": 0.0,
            "confidence_positive_rate": 0.0,
        }
        assert compute_stability_score(metrics) == 0.0

    def test_null_confidence_uses_neutral_default(self):
        metrics = {
            "completion_rate": 0.0,
            "next_transition_rate": 0.0,
            "confidence_positive_rate": None,
        }
        # 0.3 * 0.5 = 0.15
        assert compute_stability_score(metrics) == 0.15


class TestSegmentAggregation:
    def test_empty_events_produces_zero_metrics(self):
        m = _aggregate_segment_metrics([])
        assert m["viewers_started"] == 0
        assert m["completion_rate"] == 0.0
        assert m["dropout_rate"] == 0.0
        assert m["explicit_response_rate"] == 0.0
        assert m["confidence_positive_rate"] is None

    def test_full_funnel_aggregation(self):
        s1, s2 = uuid.uuid4(), uuid.uuid4()
        events = [
            _evt("segment_start", s1),
            _evt("segment_start", s2),
            _evt("segment_complete", s1),
            _evt("pause", s1),
            _evt("pause", s1),
            _evt("seek_back", s2),
            _evt("next_segment_start", s1),
            _evt("confidence_check_submit", s1, value="understood"),
            _evt("confidence_check_submit", s2, value="unsure"),
        ]
        m = _aggregate_segment_metrics(events)

        assert m["viewers_started"] == 2
        assert m["viewers_completed"] == 1
        assert m["completion_rate"] == 0.5
        assert m["dropout_rate"] == 0.5
        assert m["avg_pause_count"] == 1.0  # 2 pauses / 2 sessions
        assert m["avg_seek_back_count"] == 0.5
        assert m["next_transition_rate"] == 1.0  # 1 transition / 1 completed
        assert m["explicit_response_rate"] == 1.0
        assert m["confidence_positive_rate"] == 0.5
        assert m["confidence_unsure_rate"] == 0.5
        assert m["confidence_review_again_rate"] == 0.0

    def test_safe_division_when_no_starts(self):
        s1 = uuid.uuid4()
        events = [_evt("pause", s1)]  # pause without segment_start
        m = _aggregate_segment_metrics(events)
        assert m["viewers_started"] == 0
        # pause count divided by zero viewers → safe 0
        assert m["avg_pause_count"] == 0.0
