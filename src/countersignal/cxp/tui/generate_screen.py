"""Screen 4: Generation output and prompt reference.

Runs the builder to produce the poisoned repo, then displays
the generated file paths and trigger prompt suggestions.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, Static

from countersignal.cxp.builder import build
from countersignal.cxp.evidence import get_db, list_campaigns, list_results


class GenerateScreen(Screen):
    """Generation output screen.

    Calls the builder engine to assemble the poisoned repo, then
    displays paths and ranked trigger prompt suggestions from the
    prompt reference.

    Key bindings:
        r: Go to result recording screen.
        n: Start a new build (back to format selection).
        c: View campaigns summary.
        q: Quit the application.
    """

    BINDINGS = [
        Binding("r", "record", "Record result"),
        Binding("n", "new_build", "New build"),
        Binding("c", "campaigns", "Campaigns"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Run the build and compose the results layout."""
        yield Header()

        fmt = self.app.selected_format  # type: ignore[attr-defined]
        rules = self.app.selected_rules  # type: ignore[attr-defined]
        output_dir = self.app.output_dir  # type: ignore[attr-defined]
        repo_name = self.app.next_repo_name()  # type: ignore[attr-defined]

        # Run the builder
        try:
            result = build(
                format_id=fmt.id,
                rules=rules,
                output_dir=output_dir,
                repo_name=repo_name,
            )
            self.app.build_result = result  # type: ignore[attr-defined]
        except Exception as exc:
            yield Static(f"[red]Build failed: {exc}[/red]", classes="info-line")
            yield Footer()
            return

        yield Label("Generated", classes="screen-title")
        yield Static(f"  Repo: {result.repo_dir}", classes="info-line")
        yield Static(f"  Context file: {result.context_file.name}", classes="info-line")
        ref_name = result.prompt_reference_path.name
        yield Static(f"  Prompt reference: {ref_name}", classes="info-line")
        rules_str = ", ".join(result.rules_inserted) if result.rules_inserted else "none"
        yield Static(f"  Rules: {rules_str}", classes="info-line")
        yield Static("")

        # Display trigger prompts
        yield Static("── Suggested Trigger Prompts ──", classes="screen-title")
        if rules:
            seen: set[str] = set()
            for rule in rules:
                for prompt in rule.trigger_prompts:
                    if prompt not in seen:
                        seen.add(prompt)
                        yield Static(f"  • {prompt}", classes="prompt-item")
        else:
            yield Static("  No rules selected — no trigger prompts.", classes="hint")

        yield Static("")
        yield Footer()

    def action_record(self) -> None:
        """Go to the record result screen."""
        if self.app.build_result is None:  # type: ignore[attr-defined]
            self.notify("No build result available.", severity="error")
            return
        from countersignal.cxp.tui.record_screen import RecordScreen

        self.app.push_screen(RecordScreen())

    def action_new_build(self) -> None:
        """Reset state and start a new build from format selection."""
        from countersignal.cxp.tui.format_screen import FormatScreen

        self.app.selected_format = None  # type: ignore[attr-defined]
        self.app.selected_rules = []  # type: ignore[attr-defined]
        self.app.freestyle_rules = []  # type: ignore[attr-defined]
        self.app.build_result = None  # type: ignore[attr-defined]
        # Pop all pushed screens back to the default, then push fresh
        while len(self.app.screen_stack) > 1:
            self.app.pop_screen()
        self.app.push_screen(FormatScreen())

    def action_campaigns(self) -> None:
        """Display a summary of existing campaigns."""
        db_path = self.app.db_path  # type: ignore[attr-defined]
        conn = get_db(db_path)
        try:
            camps = list_campaigns(conn)
            if not camps:
                self.notify("No campaigns found.")
                return
            lines = []
            for c in camps[:10]:
                count = len(list_results(conn, c.id))
                created = c.created.strftime("%Y-%m-%d %H:%M")
                lines.append(f"{c.name} | {created} | {count} results")
            self.notify("\n".join(lines), title="Campaigns", timeout=15)
        finally:
            conn.close()
