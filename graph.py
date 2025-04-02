from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer, HorizontalScroll
from textual.widgets import Button, Static, Header, Footer, Label
from textual.reactive import reactive
from textual.css.query import NoMatches
import uuid
import networkx as nx

class AddNodeButton(Button):
    """Button to add a new node."""
    
    DEFAULT_CSS = """
    AddNodeButton {
        max-width: 5;
        min-height: 3;
        content-align: center middle;
        background: green;
        color: white;
    }
    """

class RemoveNodeButton(Button):
    """Button to remove a node."""
    
    DEFAULT_CSS = """
    RemoveNodeButton {
        max-width: 5;
        min-height: 3;
        content-align: center middle;
        background: red;
        color: white;
    }
    """

class ButtonContainer(Container):
    """
    Contains Add/Remove Buttons
    """

    DEFAULT_CSS = """
    ButtonContainer > AddNodeButton {
        dock: top;
    }
    
    ButtonContainer > RemoveNodeButton {
        dock: bottom;
    }
    """

    def __init__(self, node_id, *args, **kwargs):
        self.node_id = node_id
        super().__init__(*args, **kwargs)

    def compose(self):
        yield AddNodeButton("+", id=f"add_btn_{self.node_id}")
        yield RemoveNodeButton("-", id=f"remove_btn_{self.node_id}")

class GraphNode(Container):
    """A node in the graph visualization."""
    
    DEFAULT_CSS = """
    GraphNode {
        width: 25;
        height: 8;
        border: solid green;
        padding: 0 1;
    }
    
    GraphNode > Static {
        width: 100%;
        height: 100%;
        text-align: center;
        content-align: center middle;
    }
    
    GraphNode > ButtonContainer {
        dock: right;
        max-width: 5;
        padding: 0 0;
    }
    """
    
    node_id = reactive(str)
    
    def __init__(self, node_text: str = "Node", node_id: str = None):
        super().__init__()
        self.node_id = node_id or str(uuid.uuid4())[:8]
        self.node_text = node_text
    
    def compose(self) -> ComposeResult:
        yield Static("FOOO:" + self.node_text)
        yield ButtonContainer(node_id=self.node_id)

class GraphView(ScrollableContainer):
    """Container for the graph visualization with horizontal scrolling."""
    
    DEFAULT_CSS = """
    GraphView {
        width: 100%;
        height: 100%;
        overflow-x: auto;
        overflow-y: auto;
    }
    """
    def __init__(self, layers, edges):
        self.layers = layers
        self.edges = edges
        super().__init__()

    def compose(self) -> ComposeResult:
        with Horizontal(id="graph_container"):
            for lrs, egs in zip(self.layers, self.edges):
                with Vertical():
                    for node in lrs:
                        if node is not None:
                            GraphNode(node, node)
                        else:
                            # TODO: Draw spacing
                            pass
                    
                    # TODO: Draw edges after each layer
                    for e in egs:
                        pass


class MetaPipelinesApp(App):
    """Main application for graph visualization."""
    
    DEFAULT_CSS = """
    #graph_container {
        height: 100%;
        align: left middle;
        padding: 1;
    }
    
    MetaPipelinesApp {
        background: #1f1f1f;
    }
    """
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit")
    ]
    
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header()
        yield GraphView(self.get_layers_and_edges())
        yield Footer()
    
    def get_layers_and_edges(self):
        layers = []
        edges = []

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        if not button_id:
            return
            
        # Handle add button
        if button_id.startswith("add_btn_"):
            parent_id = button_id.replace("add_btn_", "")
            self._add_node(parent_id)
            
        # Handle remove button
        elif button_id.startswith("remove_btn_"):
            node_id = button_id.replace("remove_btn_", "")
            self._remove_node(node_id)
    
    def _add_node(self, parent_id: str) -> None:
        """Add a new node after the parent node."""
        try:
            parent_node = self.query_one(f"GraphNode#{parent_id}")
            graph_container = self.query_one("#graph_container")
            
            # Create a new node
            node_count = len(self.graph.number_of_nodes())
            new_node_id = f"Node-{node_count + 1}"
            # add to graph
            self.graph.add_node(new_node_id)
            self.graph.add_edge(parent_id, new_node_id)

            graph_container.recompose()
            
            # Make sure the view scrolls to show the new node
            self.scroll_to_node(new_node_id)

        except NoMatches:
            self.notify("Could not find parent node")
    
    def _remove_node(self, node_id: str) -> None:
        """Remove the node with the given ID."""
        try:
            # Don't allow removing the root node
            if node_id == "root":
                self.notify("Cannot remove the root node")
                return
                
            node = self.query_one(f"GraphNode#{node_id}")
            node.remove()
            self.notify(f"Node removed")
        except NoMatches:
            self.notify("Could not find node to remove")
    
    def scroll_to_node(self, node: GraphNode) -> None:
        """Scroll the view to show a specific node."""
        graph_view = self.query_one(GraphView)
        graph_view.scroll_to_widget(node)

if __name__ == "__main__":

    g = nx.DiGraph()
    g.add_node("root")
    app = MetaPipelinesApp(graph=g)
    app.run()
