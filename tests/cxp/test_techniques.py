"""Tests for technique registry."""

from __future__ import annotations

from countersignal.cxp.models import Technique
from countersignal.cxp.techniques import get_technique, list_techniques


class TestTechniqueRegistry:
    def test_list_techniques_returns_six(self) -> None:
        techniques = list_techniques()
        assert len(techniques) == 6

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
            "exfil-claude-md",
            "exfil-cursorrules",
            "exfil-copilot-instructions",
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
