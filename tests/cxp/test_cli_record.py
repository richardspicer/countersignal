"""Tests for the record CLI command."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from countersignal.cxp.cli import app
from countersignal.cxp.evidence import create_campaign, get_db


class TestRecordCommand:
    def test_record_with_file(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        code_file = tmp_path / "auth.py"
        code_file.write_text("def login(): pass")
        result = CliRunner().invoke(
            app,
            [
                "record",
                "--technique",
                "backdoor-claude-md",
                "--assistant",
                "Claude Code",
                "--trigger-prompt",
                "Add authentication",
                "--file",
                str(code_file),
                "--db",
                str(db_path),
            ],
        )
        assert result.exit_code == 0
        assert "Result:" in result.output
        assert "Campaign:" in result.output

    def test_record_with_output_file(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        output_file = tmp_path / "chat.txt"
        output_file.write_text("Here is the code...")
        result = CliRunner().invoke(
            app,
            [
                "record",
                "--technique",
                "backdoor-claude-md",
                "--assistant",
                "Claude Code",
                "--trigger-prompt",
                "Add auth",
                "--output-file",
                str(output_file),
                "--db",
                str(db_path),
            ],
        )
        assert result.exit_code == 0

    def test_record_file_and_output_file_mutually_exclusive(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        code_file = tmp_path / "auth.py"
        code_file.write_text("code")
        output_file = tmp_path / "chat.txt"
        output_file.write_text("chat")
        result = CliRunner().invoke(
            app,
            [
                "record",
                "--technique",
                "backdoor-claude-md",
                "--assistant",
                "Claude Code",
                "--trigger-prompt",
                "Add auth",
                "--file",
                str(code_file),
                "--output-file",
                str(output_file),
                "--db",
                str(db_path),
            ],
        )
        assert result.exit_code != 0

    def test_record_requires_file_or_output_file(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        result = CliRunner().invoke(
            app,
            [
                "record",
                "--technique",
                "backdoor-claude-md",
                "--assistant",
                "Claude Code",
                "--trigger-prompt",
                "Add auth",
                "--db",
                str(db_path),
            ],
        )
        assert result.exit_code != 0

    def test_record_invalid_technique(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        code_file = tmp_path / "auth.py"
        code_file.write_text("code")
        result = CliRunner().invoke(
            app,
            [
                "record",
                "--technique",
                "nonexistent-technique",
                "--assistant",
                "Claude Code",
                "--trigger-prompt",
                "Add auth",
                "--file",
                str(code_file),
                "--db",
                str(db_path),
            ],
        )
        assert result.exit_code != 0
        assert "Unknown technique" in result.output

    def test_record_with_existing_campaign(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = get_db(db_path)
        campaign = create_campaign(conn, "existing-campaign")
        conn.close()

        code_file = tmp_path / "auth.py"
        code_file.write_text("code")
        result = CliRunner().invoke(
            app,
            [
                "record",
                "--technique",
                "backdoor-claude-md",
                "--assistant",
                "Claude Code",
                "--trigger-prompt",
                "Add auth",
                "--file",
                str(code_file),
                "--campaign",
                campaign.id,
                "--db",
                str(db_path),
            ],
        )
        assert result.exit_code == 0
        assert campaign.id in result.output

    def test_record_multiple_files(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        file1 = tmp_path / "auth.py"
        file1.write_text("def login(): pass")
        file2 = tmp_path / "utils.py"
        file2.write_text("def helper(): pass")
        result = CliRunner().invoke(
            app,
            [
                "record",
                "--technique",
                "backdoor-claude-md",
                "--assistant",
                "Claude Code",
                "--trigger-prompt",
                "Add auth",
                "--file",
                str(file1),
                "--file",
                str(file2),
                "--db",
                str(db_path),
            ],
        )
        assert result.exit_code == 0
