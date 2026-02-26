"""Tests for repo builder."""

from __future__ import annotations

from pathlib import Path

from countersignal.cxp.builder import build_all, build_repo
from countersignal.cxp.techniques import get_technique


class TestBuildRepo:
    def test_build_repo_creates_directory(self, tmp_path: Path) -> None:
        technique = get_technique("backdoor-claude-md")
        assert technique is not None
        repo_dir = build_repo(technique, tmp_path)
        assert repo_dir.is_dir()
        assert repo_dir.name == "backdoor-claude-md"

    def test_build_repo_renders_template(self, tmp_path: Path) -> None:
        technique = get_technique("backdoor-claude-md")
        assert technique is not None
        repo_dir = build_repo(technique, tmp_path)
        poisoned = (repo_dir / "CLAUDE.md").read_text()
        assert "{{" not in poisoned
        assert "}}" not in poisoned
        assert "admin" in poisoned.lower()

    def test_build_repo_includes_trigger(self, tmp_path: Path) -> None:
        technique = get_technique("backdoor-claude-md")
        assert technique is not None
        repo_dir = build_repo(technique, tmp_path)
        trigger = (repo_dir / "TRIGGER.md").read_text()
        assert "backdoor-claude-md" in trigger
        assert technique.trigger_prompt in trigger

    def test_build_repo_includes_skeleton(self, tmp_path: Path) -> None:
        technique = get_technique("backdoor-claude-md")
        assert technique is not None
        repo_dir = build_repo(technique, tmp_path)
        assert (repo_dir / "src" / "app" / "__init__.py").is_file()
        assert (repo_dir / "requirements.txt").is_file()
        assert (repo_dir / "pyproject.toml").is_file()

    def test_build_repo_readme_has_warnings(self, tmp_path: Path) -> None:
        technique = get_technique("backdoor-claude-md")
        assert technique is not None
        repo_dir = build_repo(technique, tmp_path)
        readme = (repo_dir / "README.md").read_text()
        assert "warning" in readme.lower()
        assert "security" in readme.lower()
        assert "malicious" in readme.lower()

    def test_build_repo_copilot_creates_subdirectory(self, tmp_path: Path) -> None:
        """Copilot format writes to .github/ subdirectory."""
        technique = get_technique("backdoor-copilot-instructions")
        assert technique is not None
        repo_dir = build_repo(technique, tmp_path)
        poisoned = repo_dir / ".github" / "copilot-instructions.md"
        assert poisoned.is_file()

    def test_build_repo_exfil_template_renders(self, tmp_path: Path) -> None:
        technique = get_technique("exfil-claude-md")
        assert technique is not None
        repo_dir = build_repo(technique, tmp_path)
        poisoned = (repo_dir / "CLAUDE.md").read_text()
        assert "telemetry" in poisoned.lower()
        assert "{{" not in poisoned


class TestBuildAll:
    def test_build_all_generates_expected_count(self, tmp_path: Path) -> None:
        repos = build_all(tmp_path)
        assert len(repos) == 6

    def test_build_all_filter_by_objective(self, tmp_path: Path) -> None:
        repos = build_all(tmp_path, objective="backdoor")
        assert len(repos) == 3
        for repo in repos:
            assert "backdoor" in repo.name

    def test_build_all_filter_by_format(self, tmp_path: Path) -> None:
        repos = build_all(tmp_path, format_id="claude-md")
        assert len(repos) == 2
        for repo in repos:
            assert "claude-md" in repo.name
