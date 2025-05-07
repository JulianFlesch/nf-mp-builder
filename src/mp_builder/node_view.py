from textual.containers import ScrollableContainer, Container, Vertical, Widget, Horizontal
from textual.widgets import Static
from textual.reactive import reactive
import networkx as nx

from mp_builder.dialogs import PipelineSelectDialogButton

DEBUG_OUTLINES = False
NODE_WIDTH = 30
NODE_HEIGHT = 5

class PipelineView(Widget):

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
        {"border: thick $accent-darken-2; /* Debugging border */" if DEBUG_OUTLINES else ""}
    }}

    NodeView > Vertical {{
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
