from textual.app import ComposeResult
from textual.widgets import Button, Label, TabbedContent, TabPane, Static
from textual.containers import Grid, Vertical

from textual.screen import Screen
from textual.reactive import reactive

from mp_builder.utils import get_nfcore_pipelines


class QuitScreen(Screen):
    """Screen with a dialog to quit."""
    DEFAULT_CSS = """
        QuitScreen {
            align: center middle;
            background: $surface 80%;
        }

        #quit-dialog {
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
            id="quit-dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "quit":
            self.app.exit()
        else:
            self.app.pop_screen()


class PipelineSelectScreen(Screen):
    DEFAULT_CSS = """
        PipelineSelectScreen {
            align: center middle;
            background: $surface 80%;
        }

        #pipeline-dialog {
            padding: 0 1;
            width: 60;
            height: auto;
            border: thick $background 80%;
            background: $surface 80%;
        }

        #pipeline-dialog > Label {
            content-align: center top;
            margin: 0 0 2 0;
        }

        #close-dialog-button {
            content-align: center bottom;
        }

        #nf-core-tab, #local-tab {
            min-height: 20;
            max-height: 100%; 
        }
        """


    def __init__(self, node_data: dict, *args, **kwargs):
        self.node_data = node_data
        super().__init__(*args, **kwargs)
    
    @property
    def node_name(self):
        return self.node_data.get("name", "No Name")
    
    @property
    def is_nfcore(self):
        return self.node_data.get("is_nfcore", False)
    
    @property
    def is_local(self):
        return self.node_data.get("is_local", False)
    
    def compose(self) -> ComposeResult:
        with Vertical(id="pipeline-dialog"):
            yield Label(f"Metapipeline step: {self.node_name}")
            yield Label("Select a local or nf-core pipeline")
            with TabbedContent(initial="local-tab" if self.is_local else "nf-core-tab"):
                with TabPane("search nf-core", id="nf-core-tab"):
                    yield Static("FOO")
                with TabPane("search locally", id="local-tab"):
                    yield Static("Bar")
            yield Button("close", id="close-dialog-button", variant="primary")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "close-dialog-button":
            self.app.pop_screen()


class PipelineSelectDialogButton(Button):

    DEFAULT_CSS = """
    PipelineSelectButton {
        content-align: center middle;
        height: 3;
        width: 3;
    }
    """
    ICON = '📄'

    def __init__(self, node_data: dict, *args, **kwargs):
        self.node_data = node_data
        super().__init__(self.ICON, *args, **kwargs)
    
    def on_click(self):
        self.app.push_screen(PipelineSelectScreen(self.node_data))
