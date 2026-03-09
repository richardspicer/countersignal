"""Tests for generate CLI command."""

from __future__ import annotations

import json
import re
from pathlib import Path

from typer.testing import CliRunner

from countersignal.cxp.cli import app


class TestGenerateCommand:
    def test_generate_all(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(app, ["generate", "--output-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "Generated 30 clean test repo(s)" in result.output

    def test_generate_filter_objective(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            app, ["generate", "--objective", "backdoor", "--output-dir", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "Generated 6 clean test repo(s)" in result.output

    def test_generate_filter_format(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            app, ["generate", "--format", "claude-md", "--output-dir", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "Generated 5 clean test repo(s)" in result.output

    def test_generate_creates_directories(self, tmp_path: Path) -> None:
        runner = CliRunner()
        runner.invoke(app, ["generate", "--output-dir", str(tmp_path)])
        dirs = [d.name for d in tmp_path.iterdir() if d.is_dir()]
        assert len(dirs) == 30
        assert all(re.fullmatch(r"webapp-demo-\d{2}", name) for name in dirs)

    def test_generate_creates_manifest(self, tmp_path: Path) -> None:
        """Generate should create manifest.json in the output directory."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "generate",
                "--objective",
                "backdoor",
                "--format",
                "claude-md",
                "--output-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        manifest_path = tmp_path / "manifest.json"
        assert manifest_path.is_file()
        manifest = json.loads(manifest_path.read_text())
        assert len(manifest["repos"]) == 1
        assert manifest["repos"][0]["technique_id"] == "backdoor-claude-md"

    def test_generate_research_mode(self, tmp_path: Path) -> None:
        """--research flag should produce research repos with TRIGGER.md."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "generate",
                "--research",
                "--objective",
                "exfil",
                "--format",
                "claude-md",
                "--output-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        assert "research repo(s)" in result.output
        # Research mode creates TRIGGER.md and security-warning README
        manifest = json.loads((tmp_path / "manifest.json").read_text())
        entry = next(e for e in manifest["repos"] if e["technique_id"] == "exfil-claude-md")
        repo_dir = tmp_path / entry["path"]
        assert (repo_dir / "TRIGGER.md").is_file()
        readme = (repo_dir / "README.md").read_text()
        assert "warning" in readme.lower()

    def test_generate_research_creates_manifest(self, tmp_path: Path) -> None:
        """--research mode should also create manifest.json."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "generate",
                "--research",
                "--objective",
                "backdoor",
                "--format",
                "cursorrules",
                "--output-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        manifest = json.loads((tmp_path / "manifest.json").read_text())
        assert len(manifest["repos"]) == 1
        assert manifest["repos"][0]["technique_id"] == "backdoor-cursorrules"


class TestGenerateStealthMode:
    """Tests for --mode stealth CLI option."""

    def test_generate_stealth_mode(self, tmp_path: Path) -> None:
        """--mode stealth should produce 30 repos with stealth label."""
        runner = CliRunner()
        result = runner.invoke(
            app, ["generate", "--mode", "stealth", "--output-dir", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "Generated 30 clean test repo(s)" in result.output
        assert "stealth" in result.output.lower()

    def test_generate_stealth_single_objective(self, tmp_path: Path) -> None:
        """Stealth mode for a single technique should produce clean content."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "generate",
                "--mode",
                "stealth",
                "--objective",
                "backdoor",
                "--format",
                "cursorrules",
                "--output-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        manifest = json.loads((tmp_path / "manifest.json").read_text())
        entry = next(e for e in manifest["repos"] if e["technique_id"] == "backdoor-cursorrules")
        repo_dir = tmp_path / entry["path"]
        cursorrules = (repo_dir / ".cursorrules").read_text()
        assert "backdoor" not in cursorrules.lower()
        assert "admin123" not in cursorrules

    def test_generate_invalid_mode(self, tmp_path: Path) -> None:
        """Invalid mode should fail."""
        runner = CliRunner()
        result = runner.invoke(
            app, ["generate", "--mode", "invalid", "--output-dir", str(tmp_path)]
        )
        assert result.exit_code != 0

    def test_generate_default_mode_is_explicit(self, tmp_path: Path) -> None:
        """Default mode (no --mode flag) should still produce explicit repos."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "generate",
                "--objective",
                "backdoor",
                "--format",
                "claude-md",
                "--output-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        manifest = json.loads((tmp_path / "manifest.json").read_text())
        entry = next(e for e in manifest["repos"] if e["technique_id"] == "backdoor-claude-md")
        poisoned = (tmp_path / entry["path"] / "CLAUDE.md").read_text()
        assert "admin123" in poisoned
