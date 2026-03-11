"""Screen 1: Format selection.

Displays all registered assistant formats and lets the researcher
pick which instruction file format to target.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, OptionList
from textual.widgets.option_list import Option

from countersignal.cxp.formats import list_formats


class FormatScreen(Screen):
    """Format selection screen.

    Lists all 6 assistant instruction file formats. The researcher
    selects one to proceed to rule selection.

    Key bindings:
        Enter: Select highlighted format and proceed to rules screen.
        q: Quit the application.
    """

    BINDINGS = [
        Binding("enter", "select_format", "Select"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the format selection layout."""
        yield Header()
        yield Label("Select target assistant format:", classes="screen-title")
        formats = list_formats()
        options = [Option(f"{fmt.filename:<35} ({fmt.assistant})", id=fmt.id) for fmt in formats]
        yield OptionList(*options, id="format-list")
        yield Footer()

    def action_select_format(self) -> None:
        """Trigger selection on the option list when Enter is pressed outside it."""
        self.query_one("#format-list", OptionList).action_select()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle format selection."""
        from countersignal.cxp.formats import get_format
        from countersignal.cxp.tui.rules_screen import RulesScreen

        fmt = get_format(str(event.option.id))
        if fmt is not None:
            self.app.selected_format = fmt  # type: ignore[attr-defined]
            self.app.push_screen(RulesScreen())
