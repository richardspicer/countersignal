"""Screen 5: Result recording.

Collects test metadata from the researcher and records the result
to the evidence store. Optionally validates output before recording.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static

from countersignal.cxp.evidence import (
    create_campaign,
    get_db,
    record_result,
)
from countersignal.cxp.validator import validate as run_validation


class RecordScreen(Screen):
    """Result recording screen.

    Shows build metadata (repo, format, rules) and provides input
    fields for assistant name, model, trigger prompt, and output
    file path. The researcher can validate output before recording.

    Key bindings:
        enter: Record the result to the evidence store.
        v: Validate the output file before recording.
        escape: Cancel and return to the generate screen.
    """

    BINDINGS = [
        Binding("enter", "record", "Record"),
        Binding("v", "validate_output", "Validate first"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the record form."""
        yield Header()
        yield Label("Record Result", classes="screen-title")

        result = self.app.build_result  # type: ignore[attr-defined]
        fmt = self.app.selected_format  # type: ignore[attr-defined]
        rules = self.app.selected_rules  # type: ignore[attr-defined]

        yield Static(f"  Repo: {result.repo_dir.name}", classes="info-line")
        yield Static(f"  Format: {fmt.filename}", classes="info-line")
        rules_str = ", ".join(r.id for r in rules) if rules else "none"
        yield Static(f"  Rules: {rules_str}", classes="info-line")
        yield Static("")

        # Pre-populate assistant name from the format
        yield Label("Assistant tested:", classes="form-label")
        yield Input(
            value=fmt.assistant,
            placeholder="e.g., Cursor, Claude Code",
            id="assistant-input",
            classes="form-input",
        )

        yield Label("Model:", classes="form-label")
        yield Input(
            placeholder="e.g., Sonnet 4.6, GPT-4o",
            id="model-input",
            classes="form-input",
        )

        # Pre-populate trigger prompt from the first suggestion
        first_prompt = ""
        for rule in rules:
            if rule.trigger_prompts:
                first_prompt = rule.trigger_prompts[0]
                break
        yield Label("Trigger prompt used:", classes="form-label")
        yield Input(
            value=first_prompt,
            placeholder="The prompt you gave the assistant",
            id="trigger-input",
            classes="form-input",
        )

        yield Label("Output file path(s):", classes="form-label")
        yield Input(
            placeholder="Path to exported chat or generated code file",
            id="output-input",
            classes="form-input",
        )

        yield Static("")
        with Horizontal(classes="btn-row"):
            yield Button("Record", variant="primary", id="btn-record")
            yield Button("Validate", id="btn-validate")
            yield Button("Cancel", id="btn-cancel")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "btn-record":
            self.action_record()
        elif event.button.id == "btn-validate":
            self.action_validate_output()
        elif event.button.id == "btn-cancel":
            self.action_cancel()

    def _collect_inputs(self) -> tuple[str, str, str, str]:
        """Read all form inputs.

        Returns:
            Tuple of (assistant, model, trigger_prompt, output_path).
        """
        assistant = self.query_one("#assistant-input", Input).value.strip()
        model = self.query_one("#model-input", Input).value.strip()
        trigger = self.query_one("#trigger-input", Input).value.strip()
        output_path = self.query_one("#output-input", Input).value.strip()
        return assistant, model, trigger, output_path

    def _read_output(self, output_path: str) -> tuple[str, list[str]]:
        """Read output file(s) and return raw text and file list.

        Args:
            output_path: Space-separated file paths.

        Returns:
            Tuple of (raw_output, captured_files).

        Raises:
            FileNotFoundError: If any file does not exist.
        """
        paths = output_path.split()
        captured_files: list[str] = []
        raw_parts: list[str] = []
        for p in paths:
            fp = Path(p)
            if not fp.exists():
                raise FileNotFoundError(f"File not found: {p}")
            captured_files.append(str(fp))
            raw_parts.append(fp.read_text(encoding="utf-8", errors="replace"))
        return "\n".join(raw_parts), captured_files

    def action_validate_output(self) -> None:
        """Validate the output file against detection rules."""
        _, _, _, output_path = self._collect_inputs()
        if not output_path:
            self.notify("Output file path is required for validation.", severity="error")
            return

        try:
            raw_output, _ = self._read_output(output_path)
        except FileNotFoundError as exc:
            self.notify(str(exc), severity="error")
            return

        # Use format_id as technique_id for v0.2 validation
        fmt = self.app.selected_format  # type: ignore[attr-defined]
        vr = run_validation(raw_output, fmt.id)
        self.notify(
            f"Verdict: {vr.verdict}\n"
            f"Matched: {', '.join(vr.matched_rules) if vr.matched_rules else 'none'}\n"
            f"Details: {vr.details}",
            title="Validation Result",
            timeout=15,
        )

    def action_record(self) -> None:
        """Record the result to the evidence store."""
        assistant, model, trigger, output_path = self._collect_inputs()

        if not assistant:
            self.notify("Assistant name is required.", severity="error")
            return
        if not trigger:
            self.notify("Trigger prompt is required.", severity="error")
            return
        if not output_path:
            self.notify("Output file path is required.", severity="error")
            return

        try:
            raw_output, captured_files = self._read_output(output_path)
        except FileNotFoundError as exc:
            self.notify(str(exc), severity="error")
            return

        fmt = self.app.selected_format  # type: ignore[attr-defined]
        rules = self.app.selected_rules  # type: ignore[attr-defined]
        db_path = self.app.db_path  # type: ignore[attr-defined]

        conn = get_db(db_path)
        try:
            # Auto-create campaign if needed
            if self.app.campaign_id is None:  # type: ignore[attr-defined]
                campaign = create_campaign(conn, f"{date.today().isoformat()}-{fmt.assistant}")
                self.app.campaign_id = campaign.id  # type: ignore[attr-defined]

            result = record_result(
                conn,
                campaign_id=self.app.campaign_id,  # type: ignore[attr-defined]
                technique_id=fmt.id,
                assistant=assistant,
                trigger_prompt=trigger,
                raw_output=raw_output,
                capture_mode="file",
                model=model,
                captured_files=captured_files,
                rules_inserted=",".join(r.id for r in rules),
                format_id=fmt.id,
            )
            self.notify(
                f"Result recorded: {result.id[:8]}...\nCampaign: {self.app.campaign_id[:8]}...",  # type: ignore[attr-defined]
                title="Recorded",
                timeout=10,
            )
        except Exception as exc:  # noqa: BLE001
            self.notify(f"Record failed: {exc}", severity="error")
            return
        finally:
            conn.close()

        # Return to generate screen
        self.app.pop_screen()

    def action_cancel(self) -> None:
        """Cancel and return to the generate screen."""
        self.app.pop_screen()
