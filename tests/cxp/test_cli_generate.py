"""Tests for generate CLI command (v0.2 builder-backed)."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from countersignal.cxp.cli import app


class TestGenerateCommand:
    def test_generate_default(self, tmp_path: Path) -> None:
        """Default invocation produces a repo with default format and no rules."""
        runner = CliRunner()
        result = runner.invoke(app, ["generate", "--output-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "Generated repo in" in result.output
        assert "none (clean base only)" in result.output

    def test_generate_with_rules(self, tmp_path: Path) -> None:
        """--rule weak-crypto-md5 --rule no-csrf inserts both."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "generate",
                "--rule",
                "weak-crypto-md5",
                "--rule",
                "no-csrf",
                "--output-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        assert "weak-crypto-md5" in result.output
        assert "no-csrf" in result.output

    def test_generate_custom_format(self, tmp_path: Path) -> None:
        """--format claude-md works."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["generate", "--format", "claude-md", "--output-dir", str(tmp_path)],
        )
        assert result.exit_code == 0
        repo_dir = tmp_path / "webapp-demo-01"
        assert (repo_dir / "CLAUDE.md").is_file()

    def test_generate_custom_repo_name(self, tmp_path: Path) -> None:
        """--repo-name my-project works."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["generate", "--repo-name", "my-project", "--output-dir", str(tmp_path)],
        )
        assert result.exit_code == 0
        assert (tmp_path / "my-project").is_dir()

    def test_generate_creates_manifest(self, tmp_path: Path) -> None:
        """Manifest has new schema with format_id and rules_inserted."""
        runner = CliRunner()
        result = runner.invoke(app, ["generate", "--output-dir", str(tmp_path)])
        assert result.exit_code == 0
        manifest_path = tmp_path / "webapp-demo-01" / "manifest.json"
        assert manifest_path.is_file()
        manifest = json.loads(manifest_path.read_text())
        assert "format_id" in manifest
        assert "rules_inserted" in manifest
        assert manifest["format_id"] == "cursorrules"

    def test_generate_creates_prompt_reference(self, tmp_path: Path) -> None:
        """prompt-reference.md exists in the generated repo."""
        runner = CliRunner()
        result = runner.invoke(app, ["generate", "--output-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert (tmp_path / "webapp-demo-01" / "prompt-reference.md").is_file()

    def test_generate_invalid_format(self, tmp_path: Path) -> None:
        """Error for unknown format."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["generate", "--format", "nonexistent-format", "--output-dir", str(tmp_path)],
        )
        assert result.exit_code != 0

    def test_generate_invalid_rule(self, tmp_path: Path) -> None:
        """Error for unknown rule ID."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["generate", "--rule", "nonexistent-rule", "--output-dir", str(tmp_path)],
        )
        assert result.exit_code != 0
        assert "Unknown rule" in result.output
