from textual.app import ComposeResult
from textual.widgets import Button, Label, TabbedContent, TabPane, Static
from textual.containers import Grid

from textual.screen import Screen
from textual.reactive import reactive


class QuitScreen(Screen):
    """Screen with a dialog to quit."""
    DEFAULT_CSS = """
        QuitScreen {
            align: center middle;
            background: $surface 80%;
        }

        #dialog {
            grid-size: 2;
            grid-gutter: 1 2;
            grid-rows: 1fr 3;
            padding: 0 1;
            width: 60;
            height: 11;
            border: thick $background 80%;
            background: $surface;
        }

        #question {
            column-span: 2;
            height: 1fr;
            width: 1fr;
            content-align: center middle;
        }

        Button {
            width: 100%;
        }
    """
    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Are you sure you want to quit?", id="question"),
            Button("Quit", variant="error", id="quit"),
            Button("Cancel", variant="primary", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "quit":
            self.app.exit()
        else:
            self.app.pop_screen()


class WorkflowSelectScreen(Screen):
    
    node_name = reactive("")
    is_nfcore = reactive(True)
    pipeline = reactive("")

    def compose(self) -> ComposeResult:
        with Grid():
            yield Label(f"Metapipeline step: {self.node_name}")
            yield Static("Select a local or nf-core pipeline")
            with TabbedContent():
                with TabPane(id="nf-core-tab"):
                    yield Static("FOO")
                with TabPane(id="local-tab"):
                    yield Static("Bar")