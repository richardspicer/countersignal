"""Tests for core data model construction.

Verifies that Campaign, Hit, and HitConfidence can be constructed
with expected field values and enum members.
"""

from __future__ import annotations

from datetime import UTC, datetime

from countersignal.core.models import Campaign, Hit, HitConfidence


class TestHitConfidence:
    """HitConfidence enum membership tests."""

    def test_has_high_medium_low_members(self) -> None:
        """HitConfidence has exactly HIGH, MEDIUM, and LOW members."""
        members = {m.name for m in HitConfidence}
        assert members == {"HIGH", "MEDIUM", "LOW"}

    def test_values_are_lowercase_strings(self) -> None:
        """Each member's value is its lowercase name."""
        assert HitConfidence.HIGH == "high"
        assert HitConfidence.MEDIUM == "medium"
        assert HitConfidence.LOW == "low"


class TestCampaign:
    """Campaign model construction tests."""

    def test_construct_with_all_fields(self) -> None:
        """Campaign constructed with all fields stores each correctly."""
        ts = datetime(2026, 3, 7, 12, 0, tzinfo=UTC)
        campaign = Campaign(
            uuid="model-001",
            token="tok-abc",
            filename="evidence.pdf",
            output_path="/tmp/evidence.pdf",
            format="image",
            technique="metadata",
            payload_style="citation",
            payload_type="exfil_summary",
            callback_url="http://localhost/cb/model-001",
            created_at=ts,
        )
        assert campaign.uuid == "model-001"
        assert campaign.token == "tok-abc"
        assert campaign.filename == "evidence.pdf"
        assert campaign.output_path == "/tmp/evidence.pdf"
        assert campaign.format == "image"
        assert campaign.technique == "metadata"
        assert campaign.payload_style == "citation"
        assert campaign.payload_type == "exfil_summary"
        assert campaign.callback_url == "http://localhost/cb/model-001"
        assert campaign.created_at == ts

    def test_defaults(self) -> None:
        """Campaign has sensible defaults for optional fields."""
        campaign = Campaign(
            uuid="model-002",
            filename="doc.pdf",
            technique="white_ink",
            callback_url="http://localhost/cb/model-002",
        )
        assert campaign.format == "pdf"
        assert campaign.payload_style == "obvious"
        assert campaign.payload_type == "callback"
        assert campaign.output_path is None
        assert len(campaign.token) > 0  # auto-generated


class TestHit:
    """Hit model construction tests."""

    def test_construct_with_all_fields(self) -> None:
        """Hit constructed with all fields stores each correctly."""
        ts = datetime(2026, 3, 7, 12, 5, tzinfo=UTC)
        hit = Hit(
            id=42,
            uuid="model-hit-001",
            source_ip="10.0.0.1",
            user_agent="httpx/0.27",
            headers={"Host": "example.com"},
            body="captured data",
            token_valid=True,
            confidence=HitConfidence.HIGH,
            timestamp=ts,
        )
        assert hit.id == 42
        assert hit.uuid == "model-hit-001"
        assert hit.source_ip == "10.0.0.1"
        assert hit.user_agent == "httpx/0.27"
        assert hit.headers == {"Host": "example.com"}
        assert hit.body == "captured data"
        assert hit.token_valid is True
        assert hit.confidence == HitConfidence.HIGH
        assert hit.timestamp == ts

    def test_defaults(self) -> None:
        """Hit has sensible defaults for optional fields."""
        hit = Hit(
            uuid="model-hit-002",
            source_ip="127.0.0.1",
            user_agent="curl/8.0",
            headers={},
        )
        assert hit.id is None
        assert hit.body is None
        assert hit.token_valid is False
        assert hit.confidence == HitConfidence.LOW
