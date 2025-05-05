import os

from textual.app import ComposeResult
from textual.widgets import Button, Label, TabbedContent, TabPane, Static, Input, RadioSet, RadioButton, Markdown
from textual.containers import Grid, Vertical, Horizontal, VerticalScroll

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
            max-height: 80%;
            min-height: 10;
            border: thick $background 80%;
            background: $surface 80%;
        }

        #pipeline-dialog > Label {
            content-align: center top;
            width: auto;
            height: 3;
            margin: 0 0 1 0;
        }

        #close-dialog-button, #confirm-dialog-button {
            content-align: center bottom;
            margin: 1 2;
        }

        #tab-container {
            max-height: 50%
        }

        #nf-core-tab, #local-tab {
            min-height: 10;
            height: auto;
            border: solid grey; 
        }
        """

    def __init__(self, node_data: dict, *args, **kwargs):
        self.node_data = node_data
        self.selected_pipeline = {
            "name": self.pipeline_name,
            "location": self.pipeline_location,
            "description": self.pipeline_description
        }
        self._nf_core_pipelines = get_nfcore_pipelines()
        super().__init__(*args, **kwargs)
    

    @property
    def node_name(self):
        return self.node_data.get("name", "")
    
    @node_name.setter
    def node_name(self, value):
        self.node_data["name"] = value

    @property
    def pipeline_name(self):
        return self.node_data.get("pipeline_name", "")

    @pipeline_name.setter
    def pipeline_name(self, value: str):
        self.node_data["pipeline_name"] = value
    
    @property
    def pipeline_location(self):
        return self.node_data.get("pipeline_location", "")
    
    @pipeline_location.setter
    def pipeline_location(self, value: str):
        self.node_data["pipeline_location"] = value

    @property
    def pipeline_description(self):
        return self.node_data.get("pipeline_description", "")
    
    @pipeline_description.setter
    def pipeline_description(self, value: str):
        self.node_data["pipeline_description"] = value

    @property
    def is_nfcore(self):
        return self.node_data.get("is_nfcore", False)
    
    @is_nfcore.setter
    def is_nfcore(self, val: bool):
        self.node_data["is_nfcore"] = val

    @property
    def dialog_text(self):
        if not self.selected_pipeline.get("name", False):
            return "Select a local or nf-core pipeline"
        
        return f"[{self.selected_pipeline.get("name", "")}]({self.selected_pipeline.get("location", "")})" + \
            f"selected { os.linesep + os.linesep } {self.selected_pipeline.get("description")}"

    @property
    def nf_core_pipelines_filtered(self):
        return self._nf_core_pipelines
    
    def compose(self) -> ComposeResult:
        with Vertical(id="pipeline-dialog"):
            yield Label(f"Pipeline step: {self.node_name}")
            yield Markdown(self.dialog_text, id="pipeline-dialog-text")

            with TabbedContent(id="tab-container"):
                with TabPane("search nf-core", id="nf-core-tab"):
                    with VerticalScroll():
                        with RadioSet(id="nf-core-pipelines-list"):
                            for p in self.nf_core_pipelines_filtered:
                                yield RadioButton(p["name"], value=(p["location"] == self.pipeline_location))

                with TabPane("search locally", id="local-tab", disabled=True):
                    with VerticalScroll():
                        yield Static("Local Pipelines are currently not supported")

            with Horizontal():
                yield Button("confirm", id="confirm-dialog-button", variant="success")
                yield Button("close", id="close-dialog-button", variant="primary")

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        self.selected_pipeline = self.nf_core_pipelines_filtered[event.radio_set.pressed_index]

        self.query_one("#pipeline-dialog-text", Markdown).update(self.dialog_text)

        event.stop()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        #event.stop()  # TODO: Do bubble the event for now to trigger recompose

        if event.button.id == "close-dialog-button":
            self.app.pop_screen()

        elif event.button.id == "confirm-dialog-button":
            
            self.pipeline_name = self.selected_pipeline.get("name", "")
            self.node_name = self.pipeline_name if self.node_name == "" else self.node_name
            self.pipeline_location = self.selected_pipeline.get("location", "")
            self.pipeline_description = self.selected_pipeline.get("description", "")
            self.is_nfcore = True  # TODO: How to infer what was pressed dynamically?
            
            #self.app.refresh(recompose=True)  # TODO: More fine grained control? -> Bubble up the event
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
