from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.widgets import Button, Static, Header, Footer
from textual.reactive import reactive
from textual.css.query import NoMatches
import uuid

class GraphNode(Static):
    """A node in the graph visualization."""
    
    DEFAULT_CSS = """
    GraphNode {
        width: 20;
        height: 5;
        border: solid green;
        content-align: center middle;
    }
    """
    
    node_id = reactive(str)
    
    def __init__(self, node_text: str = "Node", node_id: str = None):
        super().__init__(node_text)
        self.node_id = node_id or str(uuid.uuid4())[:8]

class AddNodeButton(Button):
    """Button to add a new node."""
    
    DEFAULT_CSS = """
    AddNodeButton {
        max-width: 5;
        max-height: 3;
        content-align: center middle;
        background: green;
        color: white;
    }
    """
    
    parent_id = reactive(str)
    
    def __init__(self, parent_id: str):
        super().__init__("+")
        self.parent_id = parent_id

class NodeContainer(Container):
    """Container for a node and its add button."""
    
    DEFAULT_CSS = """
    NodeContainer {
        height: 6;
        layout: horizontal;
    }
    """
    
    node_id = reactive(str)
    
    def __init__(self, node_text: str = "Node", node_id: str = None):
        super().__init__()
        self.node_id = node_id or str(uuid.uuid4())[:8]
        self.node_text = node_text
    
    def compose(self) -> ComposeResult:
        yield GraphNode(self.node_text, self.node_id)
        yield AddNodeButton(self.node_id)

class GraphView(ScrollableContainer):
    """Container for the graph visualization with horizontal scrolling."""
    
    DEFAULT_CSS = """
    GraphView {
        width: 100%;
        height: 100%;
        overflow-x: auto;
        overflow-y: hidden;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="graph_container"):
            yield NodeContainer("Root", "root")
        yield Footer()

class GraphApp(App):
    """Main application for graph visualization."""
    
    DEFAULT_CSS = """
    #graph_container {
        height: 100%;
        align: left middle;
    }
    
    GraphApp {
        background: #1f1f1f;
    }
    """
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit")
    ]
    
    def compose(self) -> ComposeResult:
        yield GraphView()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if not isinstance(event.button, AddNodeButton):
            return
        
        # Get the parent node ID from the button
        parent_id = event.button.parent_id
        
        try:
            # Find the parent node's container
            parent_container = self.query_one(f"NodeContainer:has(GraphNode#{parent_id})")
            graph_container = self.query_one("#graph_container")
            
            # Create a new node container
            new_node_text = f"Node {len(graph_container.children) + 1}"
            new_node_container = NodeContainer(new_node_text)
            
            # Insert the new node after the parent node
            graph_container.insert_after(new_node_container, parent_container)
            
            # Make sure the view scrolls to show the new node
            self.call_after_refresh(self.scroll_to_node, new_node_container)
        except NoMatches:
            self.notify("Could not find parent node container")
    
    def scroll_to_node(self, node: Container) -> None:
        """Scroll the view to show a specific node."""
        graph_view = self.query_one(GraphView)
        graph_view.scroll_to_widget(node)

if __name__ == "__main__":
    app = GraphApp()
    app.run()
