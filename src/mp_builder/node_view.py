from textual.containers import ScrollableContainer, Container, Vertical, Widget, Horizontal
from textual.widgets import Static
from textual.reactive import reactive
import networkx as nx

from mp_builder.dialogs import PipelineSelectDialogButton

DEBUG_OUTLINES = False
NODE_WIDTH = 30
NODE_HEIGHT = 5

class PipelineView(Widget):
        
    DEFAULT_CSS = f"""
    PipelineView {{
        align: center middle;
        width: {NODE_WIDTH};
        border: solid green;
        height: {NODE_HEIGHT};
        padding: 0 0;
    }}

    PipelineView > Horizontal > Static {{
        height: 100%;
        width: 90%;
    }}

    PipelineView > Horizontal > PipelineSelectDialogButton {{
        width: 10%;
        min-width: 4;
        
    }}
    
    """

    #name = reactive("PIPELINE NAME")
    #node_data = reactive(dict())

    def __init__(self, node_id, node_data):
        self.node_id = node_id
        self.node_data = node_data
        super().__init__()

    def compose(self):
        with Horizontal():
            yield Static(self.node_data.get("name", self.node_id))
            yield PipelineSelectDialogButton(self.node_data)

    #def render(self):
    #    return f"Pipeline node: {self.name}"

class NodeView(Container):

    DEFAULT_CSS = f"""

    NodeView {{
        height: auto;
        width: auto;
        {"border: thick $accent-darken-2; /* Debugging border */" if DEBUG_OUTLINES else ""}
    }}

    NodeView > Vertical {{
        height: auto;
        width: auto;
        {"border: thick $accent-darken-2; /* Debugging border */" if DEBUG_OUTLINES else ""}
    }}
    """

    def __init__(self, graph: nx.DiGraph):
        self.graph = graph
        super().__init__()

    def compose(self):

        with Vertical():
            for i, n in enumerate(self.graph.nodes):
                yield PipelineView(n, self.graph.nodes[n])
