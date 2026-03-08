"""Behavioral tests for core database operations.

Covers campaign CRUD, hit recording and retrieval, database reset
with file cleanup, and schema migration versioning.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from countersignal.core.db import (
    get_all_campaigns,
    get_campaign,
    get_campaign_by_token,
    get_connection,
    get_hits,
    init_db,
    reset_db,
    save_campaign,
    save_hit,
)
from countersignal.core.models import Campaign, Hit, HitConfidence


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    """Create and initialize a temporary database."""
    path = tmp_path / "test.db"
    init_db(path)
    return path


def _make_campaign(uuid: str = "test-uuid", **overrides: object) -> Campaign:
    """Build a Campaign with sensible defaults, overriding any field."""
    defaults: dict[str, object] = {
        "uuid": uuid,
        "filename": "test.pdf",
        "technique": "white_ink",
        "callback_url": f"http://localhost:8080/cb/{uuid}",
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    return Campaign(**defaults)  # type: ignore[arg-type]


def _make_hit(uuid: str = "test-uuid", **overrides: object) -> Hit:
    """Build a Hit with sensible defaults, overriding any field."""
    defaults: dict[str, object] = {
        "uuid": uuid,
        "source_ip": "127.0.0.1",
        "user_agent": "python-requests/2.31",
        "headers": {"Host": "localhost"},
        "timestamp": datetime(2026, 1, 1, 0, 5, tzinfo=UTC),
    }
    defaults.update(overrides)
    return Hit(**defaults)  # type: ignore[arg-type]


class TestCampaignCrud:
    """Campaign create-read lifecycle tests."""

    def test_save_and_retrieve_by_uuid(self, db_path: Path) -> None:
        """Save a campaign and retrieve it by UUID; all fields must match."""
        campaign = _make_campaign(
            uuid="crud-001",
            token="my-secret-token",
            filename="report.pdf",
            output_path="/tmp/report.pdf",
            format="pdf",
            technique="metadata",
            payload_style="citation",
            payload_type="exfil_summary",
            callback_url="http://localhost/cb/crud-001",
            created_at=datetime(2026, 3, 7, 12, 0, tzinfo=UTC),
        )
        save_campaign(campaign, db_path)

        loaded = get_campaign("crud-001", db_path)
        assert loaded is not None
        assert loaded.uuid == campaign.uuid
        assert loaded.token == "my-secret-token"
        assert loaded.filename == "report.pdf"
        assert loaded.output_path == "/tmp/report.pdf"
        assert loaded.format == "pdf"
        assert loaded.technique == "metadata"
        assert loaded.payload_style == "citation"
        assert loaded.payload_type == "exfil_summary"
        assert loaded.callback_url == "http://localhost/cb/crud-001"
        assert loaded.created_at == datetime(2026, 3, 7, 12, 0, tzinfo=UTC)

    def test_retrieve_by_token(self, db_path: Path) -> None:
        """Retrieve a campaign by UUID+token; verify match."""
        campaign = _make_campaign(uuid="token-001", token="valid-tok")
        save_campaign(campaign, db_path)

        loaded = get_campaign_by_token("token-001", "valid-tok", db_path)
        assert loaded is not None
        assert loaded.uuid == "token-001"
        assert loaded.token == "valid-tok"

    def test_retrieve_by_wrong_token_returns_none(self, db_path: Path) -> None:
        """Wrong token returns None even if UUID exists."""
        campaign = _make_campaign(uuid="token-002", token="correct")
        save_campaign(campaign, db_path)

        assert get_campaign_by_token("token-002", "wrong", db_path) is None

    def test_list_all_campaigns(self, db_path: Path) -> None:
        """Save two campaigns, list all, verify count and newest-first order."""
        c1 = _make_campaign(uuid="list-001", created_at=datetime(2026, 1, 1, tzinfo=UTC))
        c2 = _make_campaign(uuid="list-002", created_at=datetime(2026, 1, 2, tzinfo=UTC))
        save_campaign(c1, db_path)
        save_campaign(c2, db_path)

        campaigns = get_all_campaigns(db_path)
        assert len(campaigns) == 2
        assert campaigns[0].uuid == "list-002"  # newest first
        assert campaigns[1].uuid == "list-001"

    def test_duplicate_uuid_raises_integrity_error(self, db_path: Path) -> None:
        """Inserting a campaign with a duplicate UUID raises IntegrityError."""
        save_campaign(_make_campaign(uuid="dup-001"), db_path)
        with pytest.raises(sqlite3.IntegrityError):
            save_campaign(_make_campaign(uuid="dup-001"), db_path)


class TestHitRecording:
    """Hit save and retrieval tests."""

    def test_record_and_retrieve_hit(self, db_path: Path) -> None:
        """Record a hit and retrieve it by campaign UUID; all fields match."""
        save_campaign(_make_campaign(uuid="hit-001"), db_path)
        hit = _make_hit(
            uuid="hit-001",
            source_ip="10.0.0.1",
            user_agent="curl/7.88",
            headers={"Host": "example.com", "Accept": "*/*"},
            timestamp=datetime(2026, 2, 1, 8, 0, tzinfo=UTC),
        )
        save_hit(hit, db_path)

        hits = get_hits("hit-001", db_path)
        assert len(hits) == 1
        loaded = hits[0]
        assert loaded.uuid == "hit-001"
        assert loaded.source_ip == "10.0.0.1"
        assert loaded.user_agent == "curl/7.88"
        assert loaded.headers == {"Host": "example.com", "Accept": "*/*"}
        assert loaded.timestamp == datetime(2026, 2, 1, 8, 0, tzinfo=UTC)

    def test_multiple_hits_ordered_newest_first(self, db_path: Path) -> None:
        """Multiple hits for the same campaign are returned newest-first."""
        save_campaign(_make_campaign(uuid="order-001"), db_path)
        for minute in (10, 30, 20):
            save_hit(
                _make_hit(
                    uuid="order-001",
                    timestamp=datetime(2026, 1, 1, 0, minute, tzinfo=UTC),
                ),
                db_path,
            )

        hits = get_hits("order-001", db_path)
        assert len(hits) == 3
        assert hits[0].timestamp.minute == 30
        assert hits[1].timestamp.minute == 20
        assert hits[2].timestamp.minute == 10

    def test_token_valid_and_high_confidence_roundtrip(self, db_path: Path) -> None:
        """token_valid=True and confidence=HIGH survive a save/load cycle.

        Regression test for the sqlite3.Row bug fixed in e90d3d4.
        """
        save_campaign(_make_campaign(uuid="conf-001"), db_path)
        save_hit(
            _make_hit(uuid="conf-001", token_valid=True, confidence=HitConfidence.HIGH),
            db_path,
        )

        hits = get_hits("conf-001", db_path)
        assert len(hits) == 1
        assert hits[0].token_valid is True
        assert hits[0].confidence == HitConfidence.HIGH

    def test_hit_body_roundtrip(self, db_path: Path) -> None:
        """Hit body content survives a save/load cycle."""
        save_campaign(_make_campaign(uuid="body-001"), db_path)
        save_hit(
            _make_hit(uuid="body-001", body="exfiltrated data payload"),
            db_path,
        )

        hits = get_hits("body-001", db_path)
        assert len(hits) == 1
        assert hits[0].body == "exfiltrated data payload"


class TestReset:
    """Database reset and file cleanup tests."""

    def test_reset_clears_campaigns_and_hits(self, db_path: Path) -> None:
        """reset_db empties both tables and returns correct counts."""
        save_campaign(_make_campaign(uuid="reset-001"), db_path)
        save_hit(_make_hit(uuid="reset-001"), db_path)
        save_hit(_make_hit(uuid="reset-001"), db_path)

        campaigns_del, hits_del, files_del = reset_db(db_path)

        assert campaigns_del == 1
        assert hits_del == 2
        assert files_del == 0
        assert get_all_campaigns(db_path) == []
        assert get_hits(db_path=db_path) == []

    def test_reset_deletes_generated_files(self, db_path: Path, tmp_path: Path) -> None:
        """reset_db deletes files referenced by output_path."""
        output_file = tmp_path / "generated.pdf"
        output_file.write_text("fake pdf content")
        assert output_file.is_file()

        save_campaign(
            _make_campaign(uuid="file-001", output_path=str(output_file)),
            db_path,
        )

        _, _, files_del = reset_db(db_path)

        assert files_del == 1
        assert not output_file.is_file()


class TestSchemaMigration:
    """Schema versioning tests."""

    def test_fresh_db_starts_at_schema_v4(self, db_path: Path) -> None:
        """A freshly initialized database has user_version = 4."""
        with get_connection(db_path) as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
        assert version == 4
