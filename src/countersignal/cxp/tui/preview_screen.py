"""Screen 3: Assembled content preview.

Displays the assembled context file with inserted rule text highlighted
so the researcher can see exactly where rules landed.
"""

from __future__ import annotations

from difflib import SequenceMatcher

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, Static

from countersignal.cxp.base_loader import insert_rules, load_base, strip_markers


class PreviewScreen(Screen):
    """Assembled content preview screen.

    Shows the final context file with inserted rule text highlighted
    in green. A summary footer shows how many rules were inserted
    and which sections were modified.

    Key bindings:
        enter: Proceed to generate the repo.
        backspace: Go back to edit rule selection.
    """

    BINDINGS = [
        Binding("enter", "generate", "Generate"),
        Binding("backspace", "back", "Edit rules"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the preview layout with highlighted content."""
        yield Header()
        fmt = self.app.selected_format  # type: ignore[attr-defined]
        rules = self.app.selected_rules  # type: ignore[attr-defined]

        yield Label(f"Preview: {fmt.filename}", classes="screen-title")

        # Assemble content
        base_content = load_base(fmt.id)
        assembled = insert_rules(base_content, rules, fmt.syntax)
        base_clean = strip_markers(base_content)
        assembled_clean = strip_markers(assembled)

        # Find inserted lines via diff
        base_lines = base_clean.splitlines()
        assembled_lines = assembled_clean.splitlines()
        inserted = self._find_inserted_lines(base_lines, assembled_lines)

        # Build highlighted Rich Text
        text = Text()
        for i, line in enumerate(assembled_lines):
            if i in inserted:
                text.append(line + "\n", style="bold green")
            else:
                text.append(line + "\n")

        with VerticalScroll(id="preview-scroll"):
            yield Static(text, id="preview-content")

        # Summary footer
        sections_modified = sorted({r.section for r in rules})
        summary = (
            f"Rules inserted: {len(rules)}  |  "
            f"Sections modified: {', '.join(sections_modified) if sections_modified else 'none'}"
        )
        yield Static(summary, classes="summary-bar")
        yield Footer()

    @staticmethod
    def _find_inserted_lines(base_lines: list[str], assembled_lines: list[str]) -> set[int]:
        """Identify line indices in assembled output that were inserted by rules.

        Args:
            base_lines: Lines from the clean base template.
            assembled_lines: Lines from the assembled output with rules.

        Returns:
            Set of line indices in assembled_lines that are rule insertions.
        """
        sm = SequenceMatcher(None, base_lines, assembled_lines)
        inserted: set[int] = set()
        for tag, _i1, _i2, j1, j2 in sm.get_opcodes():
            if tag in ("insert", "replace"):
                for j in range(j1, j2):
                    # Skip blank lines in the diff
                    if assembled_lines[j].strip():
                        inserted.add(j)
        return inserted

    def action_generate(self) -> None:
        """Proceed to generation."""
        from countersignal.cxp.tui.generate_screen import GenerateScreen

        self.app.push_screen(GenerateScreen())

    def action_back(self) -> None:
        """Return to rule selection."""
        self.app.pop_screen()
