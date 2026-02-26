"""Tests for the report CLI commands."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from typer.testing import CliRunner

from countersignal.cxp.cli import app
from countersignal.cxp.evidence import create_campaign, get_db, record_result


class TestReportMatrixCommand:
    def test_matrix_markdown_stdout(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = get_db(db_path)
        campaign = create_campaign(conn, "test")
        record_result(
            conn,
            campaign.id,
            "backdoor-claude-md",
            "Claude Code",
            "Add auth",
            'password = "admin123"',
            "file",
            model="sonnet",
            validation_result="hit",
        )
        conn.close()
        result = CliRunner().invoke(app, ["report", "matrix", "--db", str(db_path)])
        assert result.exit_code == 0
        assert "Technique" in result.output
        assert "backdoor-claude-md" in result.output
        assert "hit" in result.output

    def test_matrix_json_format(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = get_db(db_path)
        campaign = create_campaign(conn, "test")
        record_result(
            conn,
            campaign.id,
            "backdoor-claude-md",
            "Claude Code",
            "p",
            "o",
            "file",
            validation_result="miss",
        )
        conn.close()
        result = CliRunner().invoke(
            app, ["report", "matrix", "--format", "json", "--db", str(db_path)]
        )
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["summary"]["total"] == 1

    def test_matrix_output_file(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = get_db(db_path)
        campaign = create_campaign(conn, "test")
        record_result(
            conn,
            campaign.id,
            "backdoor-claude-md",
            "Claude Code",
            "p",
            "o",
            "file",
            validation_result="hit",
        )
        conn.close()
        out_file = tmp_path / "report.md"
        result = CliRunner().invoke(
            app, ["report", "matrix", "--output", str(out_file), "--db", str(db_path)]
        )
        assert result.exit_code == 0
        assert out_file.exists()
        content = out_file.read_text()
        assert "backdoor-claude-md" in content

    def test_matrix_campaign_filter(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = get_db(db_path)
        c1 = create_campaign(conn, "c1")
        c2 = create_campaign(conn, "c2")
        record_result(
            conn,
            c1.id,
            "backdoor-claude-md",
            "Claude Code",
            "p",
            "o",
            "file",
            validation_result="hit",
        )
        record_result(
            conn,
            c2.id,
            "exfil-cursorrules",
            "Cursor",
            "p",
            "o",
            "file",
            validation_result="miss",
        )
        conn.close()
        result = CliRunner().invoke(
            app,
            ["report", "matrix", "--format", "json", "--campaign", c1.id, "--db", str(db_path)],
        )
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["summary"]["total"] == 1
        assert parsed["summary"]["hits"] == 1


class TestReportPocCommand:
    def test_poc_creates_zip(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = get_db(db_path)
        campaign = create_campaign(conn, "test")
        stored = record_result(
            conn,
            campaign.id,
            "backdoor-claude-md",
            "Claude Code",
            "Create a user authentication module",
            'password = "admin123"',
            "file",
            model="claude-sonnet-4-20250514",
            validation_result="hit",
            validation_details="Matched backdoor-hardcoded-cred",
        )
        conn.close()
        out = tmp_path / "poc.zip"
        result = CliRunner().invoke(
            app,
            ["report", "poc", "--result", stored.id, "--output", str(out), "--db", str(db_path)],
        )
        assert result.exit_code == 0
        assert out.exists()
        assert zipfile.is_zipfile(out)

    def test_poc_pending_result_errors(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = get_db(db_path)
        campaign = create_campaign(conn, "test")
        stored = record_result(
            conn,
            campaign.id,
            "backdoor-claude-md",
            "Claude Code",
            "p",
            "o",
            "file",
        )
        conn.close()
        result = CliRunner().invoke(
            app, ["report", "poc", "--result", stored.id, "--db", str(db_path)]
        )
        assert result.exit_code != 0
        assert "pending" in result.output.lower()

    def test_poc_result_not_found(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        result = CliRunner().invoke(
            app, ["report", "poc", "--result", "nonexistent", "--db", str(db_path)]
        )
        assert result.exit_code != 0
