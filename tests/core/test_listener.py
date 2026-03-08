"""Tests for callback listener confidence scoring.

Verifies that score_confidence produces the correct HitConfidence
level based on token validity and User-Agent string analysis.
"""

from __future__ import annotations

from countersignal.core.listener import score_confidence
from countersignal.core.models import HitConfidence


class TestScoreConfidence:
    """Confidence scoring decision tree tests."""

    def test_valid_token_programmatic_ua_returns_high(self) -> None:
        """Valid token with a programmatic User-Agent scores HIGH."""
        assert score_confidence(True, "python-requests/2.31") == HitConfidence.HIGH

    def test_valid_token_browser_ua_returns_high(self) -> None:
        """Valid token with a browser User-Agent still scores HIGH.

        Token validity short-circuits; User-Agent is irrelevant when token matches.
        """
        assert score_confidence(True, "Mozilla/5.0 (Windows NT 10.0)") == HitConfidence.HIGH

    def test_invalid_token_programmatic_ua_returns_medium(self) -> None:
        """Invalid token but programmatic User-Agent scores MEDIUM."""
        assert score_confidence(False, "python-requests/2.31") == HitConfidence.MEDIUM

    def test_invalid_token_browser_ua_returns_low(self) -> None:
        """Invalid token with a browser User-Agent scores LOW."""
        assert score_confidence(False, "Mozilla/5.0 (Windows NT 10.0)") == HitConfidence.LOW

    def test_missing_token_empty_ua_returns_low(self) -> None:
        """No token and empty User-Agent scores LOW."""
        assert score_confidence(False, "") == HitConfidence.LOW

    def test_programmatic_ua_patterns_case_insensitive(self) -> None:
        """Programmatic UA matching is case-insensitive."""
        assert score_confidence(False, "Python-Requests/2.31") == HitConfidence.MEDIUM
        assert score_confidence(False, "CURL/8.0") == HitConfidence.MEDIUM
