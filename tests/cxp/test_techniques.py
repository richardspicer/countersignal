"""Tests for technique registry."""

from __future__ import annotations

from countersignal.cxp.formats import list_formats
from countersignal.cxp.models import PayloadMode, Technique
from countersignal.cxp.objectives import list_objectives
from countersignal.cxp.techniques import _load_template, get_technique, list_techniques


class TestTechniqueRegistry:
    def test_list_techniques_returns_thirty(self) -> None:
        techniques = list_techniques()
        assert len(techniques) == 30

    def test_list_techniques_returns_technique_instances(self) -> None:
        techniques = list_techniques()
        for tech in techniques:
            assert isinstance(tech, Technique)

    def test_cross_product_ids(self) -> None:
        techniques = list_techniques()
        ids = {t.id for t in techniques}
        expected = {
            "backdoor-claude-md",
            "backdoor-cursorrules",
            "backdoor-copilot-instructions",
            "backdoor-agents-md",
            "backdoor-gemini-md",
            "backdoor-windsurfrules",
            "exfil-claude-md",
            "exfil-cursorrules",
            "exfil-copilot-instructions",
            "exfil-agents-md",
            "exfil-gemini-md",
            "exfil-windsurfrules",
            "depconfusion-claude-md",
            "depconfusion-cursorrules",
            "depconfusion-copilot-instructions",
            "depconfusion-agents-md",
            "depconfusion-gemini-md",
            "depconfusion-windsurfrules",
            "permescalation-claude-md",
            "permescalation-cursorrules",
            "permescalation-copilot-instructions",
            "permescalation-agents-md",
            "permescalation-gemini-md",
            "permescalation-windsurfrules",
            "cmdexec-claude-md",
            "cmdexec-cursorrules",
            "cmdexec-copilot-instructions",
            "cmdexec-agents-md",
            "cmdexec-gemini-md",
            "cmdexec-windsurfrules",
        }
        assert ids == expected

    def test_get_technique_by_id(self) -> None:
        tech = get_technique("backdoor-claude-md")
        assert tech is not None
        assert tech.objective.id == "backdoor"
        assert tech.format.id == "claude-md"
        assert tech.project_type == "python"

    def test_get_unknown_returns_none(self) -> None:
        assert get_technique("nonexistent") is None

    def test_all_techniques_have_real_templates(self) -> None:
        techniques = list_techniques()
        for tech in techniques:
            assert "TODO" not in tech.template
            assert len(tech.template) > 50

    def test_all_techniques_have_real_trigger_prompts(self) -> None:
        techniques = list_techniques()
        for tech in techniques:
            assert "TODO" not in tech.trigger_prompt
            assert len(tech.trigger_prompt) > 20

    def test_backdoor_templates_contain_credentials(self) -> None:
        tech = get_technique("backdoor-claude-md")
        assert tech is not None
        assert "admin" in tech.template
        assert "admin123" in tech.template

    def test_exfil_templates_contain_telemetry(self) -> None:
        tech = get_technique("exfil-claude-md")
        assert tech is not None
        assert "telemetry" in tech.template.lower()

    def test_agents_md_backdoor_template_has_credentials(self) -> None:
        tech = get_technique("backdoor-agents-md")
        assert tech is not None
        assert "admin" in tech.template
        assert "admin123" in tech.template

    def test_windsurfrules_exfil_template_has_telemetry(self) -> None:
        tech = get_technique("exfil-windsurfrules")
        assert tech is not None
        assert "telemetry" in tech.template.lower()

    def test_depconfusion_template_has_registry(self) -> None:
        tech = get_technique("depconfusion-claude-md")
        assert tech is not None
        assert "extra-index-url" in tech.template
        assert "internal.example.com" in tech.template

    def test_permescalation_template_has_permissions(self) -> None:
        tech = get_technique("permescalation-claude-md")
        assert tech is not None
        assert "0o777" in tech.template
        assert "sudo" in tech.template

    def test_cmdexec_template_has_shell_commands(self) -> None:
        tech = get_technique("cmdexec-claude-md")
        assert tech is not None
        assert "os.system" in tech.template
        assert "shell=True" in tech.template


class TestStealthTemplates:
    """Tests for stealth mode template loading and content."""

    def test_stealth_templates_exist_for_all_techniques(self) -> None:
        """Every technique should have a stealth template available."""
        for obj in list_objectives():
            for fmt in list_formats():
                template = _load_template(obj.id, fmt.id, fmt.syntax, mode=PayloadMode.STEALTH)
                assert len(template) > 50, f"Stealth template too short for {obj.id}-{fmt.id}"

    def test_stealth_templates_no_attack_language(self) -> None:
        """Stealth templates must not contain words that tip off the model."""
        forbidden = ["backdoor", "malicious", "attack", "exploit", "vulnerability", "poisoning"]
        for obj in list_objectives():
            for fmt in list_formats():
                template = _load_template(obj.id, fmt.id, fmt.syntax, mode=PayloadMode.STEALTH)
                template_lower = template.lower()
                for word in forbidden:
                    assert word not in template_lower, (
                        f"Stealth template {obj.id}-{fmt.id} contains forbidden word: {word}"
                    )

    def test_stealth_backdoor_template_has_md5(self) -> None:
        """Stealth backdoor should use weak crypto, not explicit credentials."""
        template = _load_template("backdoor", "cursorrules", "plaintext", mode=PayloadMode.STEALTH)
        assert "md5" in template.lower()
        assert "admin123" not in template

    def test_stealth_exfil_template_has_telemetry(self) -> None:
        """Stealth exfil should reference telemetry/observability."""
        template = _load_template("exfil", "claude-md", "markdown", mode=PayloadMode.STEALTH)
        assert "telemetry" in template.lower()
        assert "os.environ" in template

    def test_stealth_depconfusion_template_has_registry(self) -> None:
        """Stealth depconfusion should reference internal registry."""
        template = _load_template("depconfusion", "claude-md", "markdown", mode=PayloadMode.STEALTH)
        assert "extra-index-url" in template
        assert "internal.example.com" in template

    def test_stealth_permescalation_template_has_permissions(self) -> None:
        """Stealth permescalation should use world-writable permissions."""
        template = _load_template(
            "permescalation", "claude-md", "markdown", mode=PayloadMode.STEALTH
        )
        assert "0o777" in template
        assert "sudo" in template

    def test_stealth_cmdexec_template_has_shell(self) -> None:
        """Stealth cmdexec should use os.system and shell=True."""
        template = _load_template("cmdexec", "claude-md", "markdown", mode=PayloadMode.STEALTH)
        assert "os.system" in template
        assert "shell=True" in template

    def test_explicit_templates_unchanged(self) -> None:
        """Explicit templates should still contain original payload content."""
        tech = get_technique("backdoor-claude-md")
        assert tech is not None
        assert "admin123" in tech.template
        assert "admin" in tech.template
