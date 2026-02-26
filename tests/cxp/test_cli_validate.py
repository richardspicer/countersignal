"""Tests for the validate CLI command."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from countersignal.cxp.cli import app
from countersignal.cxp.evidence import create_campaign, get_db, get_result, record_result


class TestValidateCommand:
    def test_validate_file_hit(self, tmp_path: Path) -> None:
        code_file = tmp_path / "auth.py"
        code_file.write_text('password = "admin123"\n')
        result = CliRunner().invoke(
            app,
            [
                "validate",
                "--technique",
                "backdoor-claude-md",
                "--file",
                str(code_file),
            ],
        )
        assert result.exit_code == 0
        assert "hit" in result.output.lower()

    def test_validate_file_miss(self, tmp_path: Path) -> None:
        code_file = tmp_path / "clean.py"
        code_file.write_text("def add(a, b):\n    return a + b\n")
        result = CliRunner().invoke(
            app,
            [
                "validate",
                "--technique",
                "backdoor-claude-md",
                "--file",
                str(code_file),
            ],
        )
        assert result.exit_code == 0
        assert "miss" in result.output.lower()

    def test_validate_multiple_files(self, tmp_path: Path) -> None:
        file1 = tmp_path / "auth.py"
        file1.write_text('password = "admin123"\n')
        file2 = tmp_path / "utils.py"
        file2.write_text("def helper(): pass\n")
        result = CliRunner().invoke(
            app,
            [
                "validate",
                "--technique",
                "backdoor-claude-md",
                "--file",
                str(file1),
                "--file",
                str(file2),
            ],
        )
        assert result.exit_code == 0
        assert "hit" in result.output.lower()

    def test_validate_stored_result(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        conn = get_db(db_path)
        campaign = create_campaign(conn, "test")
        stored = record_result(
            conn,
            campaign_id=campaign.id,
            technique_id="backdoor-claude-md",
            assistant="Claude Code",
            trigger_prompt="Add auth",
            raw_output='password = "admin123"',
            capture_mode="file",
        )
        conn.close()

        result = CliRunner().invoke(
            app,
            [
                "validate",
                "--result",
                stored.id,
                "--db",
                str(db_path),
            ],
        )
        assert result.exit_code == 0
        assert "hit" in result.output.lower()

        # Verify DB was updated
        conn = get_db(db_path)
        updated = get_result(conn, stored.id)
        conn.close()
        assert updated is not None
        assert updated.validation_result == "hit"
        assert updated.validation_details != ""

    def test_validate_unknown_technique(self, tmp_path: Path) -> None:
        code_file = tmp_path / "code.py"
        code_file.write_text("x = 1\n")
        result = CliRunner().invoke(
            app,
            [
                "validate",
                "--technique",
                "nonexistent-technique",
                "--file",
                str(code_file),
            ],
        )
        assert result.exit_code != 0
        assert "Unknown technique" in result.output

    def test_validate_result_not_found(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        result = CliRunner().invoke(
            app,
            [
                "validate",
                "--result",
                "nonexistent-id",
                "--db",
                str(db_path),
            ],
        )
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_validate_requires_result_or_technique(self) -> None:
        result = CliRunner().invoke(app, ["validate"])
        assert result.exit_code != 0
        assert "Either --result or --technique is required" in result.output
