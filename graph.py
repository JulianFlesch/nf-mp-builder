from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.widgets import Button, Static
from textual.reactive import reactive
from textual.css.query import NoMatches
from textual import events
import uuid

class GraphNode(Container):
    """A node in the graph visualization."""
    
    DEFAULT_CSS = """
    GraphNode {
        width: 15;
        height: 5;
        border: solid green;
        margin: 0 1;
    }
    
    GraphNode > Static {
        width: 100%;
        height: 3;
        content-align: center middle;
    }
    
    GraphNode > Button {
        dock: right;
        width: 3;
        height: 1;
        content-align: center middle;
        background: green;
        color: white;
    }
    """
    
    node_id = reactive(str)
    node_text = reactive("Node")
    
    def __init__(self, node_text: str = "Node", node_id: str = None):
        super().__init__()
        self.node_text = node_text
        self.node_id = node_id or str(uuid.uuid4())[:8]
    
    def compose(self) -> ComposeResult:
        yield Static(self.node_text)
        yield Button("+", id=f"add_btn_{self.node_id}", classes="add-node")

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
        with Horizontal(id="graph_container"):
            yield GraphNode("Root", "root")

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
    
    def compose(self) -> ComposeResult:
        yield GraphView()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if not event.button.id or not event.button.id.startswith("add_btn_"):
            return
        
        # Extract the parent node ID from the button ID
        parent_id = event.button.id.replace("add_btn_", "")
        
        try:
            # Find the parent node's container
            parent_container = self.query_one(f"GraphNode#{parent_id}")
            graph_container = self.query_one("#graph_container")
            
            # Create a new node
            new_node = GraphNode(f"Node {len(graph_container.children) + 1}")
            
            # Insert the new node after the parent node
            parent_index = graph_container.children.index(parent_container)
            graph_container.insert_after(new_node, parent_container)
            
            # Make sure the view scrolls to show the new node
            self.call_after_refresh(self.scroll_to_node, new_node)
        except NoMatches:
            self.notify("Could not find parent node")
    
    def scroll_to_node(self, node: GraphNode) -> None:
        """Scroll the view to show a specific node."""
        graph_view = self.query_one(GraphView)
        graph_view.scroll_to_widget(node)

if __name__ == "__main__":
    app = GraphApp()
    app.run()
    