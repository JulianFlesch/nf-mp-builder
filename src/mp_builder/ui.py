from textual.app import App, ComposeResult
from textual.widgets import Button, Header, Footer
from textual.css.query import NoMatches
import networkx as nx

from mp_builder.graph import GraphView

class MetaPipelinesApp(App):
    """Main application for graph visualization."""
    
    DEFAULT_CSS = """    
    MetaPipelinesApp {
        background: #1f1f1f;
    }
    """
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit"),
        ("w", "write_graph", "Save"),
        ("o", "load_graph", "Open"),
        ("z", "undo", "Undo"),
        ("y", "redo", "Redo")
    ]
    
    def __init__(self, graph: nx.DiGraph):
        self._next_node_id = 1
        self.graph = graph  #graph
        super().__init__()

    @property
    def next_node_number(self):
        nid, self._next_node_id = self._next_node_id, self._next_node_id + 1
        return nid

    def compose(self) -> ComposeResult:
        yield Header()
        yield GraphView(self.graph)  # pass reference
        yield Footer()

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
        #try:
            graph_view = self.query_one(GraphView)
            
            # Create a new node
            new_node_id = f"node{self.next_node_number}"

            # only update the original graph
            self.graph.add_edge(parent_id, new_node_id)

            # Update Graph view
            graph_view.refresh(recompose=True)
            
            # Make sure the view scrolls to show the new node
            graph_view.call_after_refresh(self.scroll_to_node, graph_view, new_node_id)

        #except NoMatches:
        #    self.notify("Could not find parent node")
    
    def _remove_node(self, node_id: str) -> None:
        """Remove the node with the given ID."""
        try:
            # Don't allow removing the root node
            if node_id == "node0":
                self.notify("Cannot remove the root node")
                return
            
            # Remove node (and all its edges)
            # TODO: Remove disconnected nodes 
            # (They won't be drawn, but are still in the graph)
            self.graph.remove_node(node_id)

            # Redraw the graph
            graph_view = self.query_one(GraphView)
            graph_view.refresh(recompose=True)

            self.notify(f"Node removed")
        except NoMatches:
            self.notify("Could not find node to remove")
    
    def scroll_to_node(self, graph_view: GraphView, node_id: str) -> None:
        """Scroll the view to show a specific node."""
        focused_graph_node = self.query_one(f"GraphNode#{node_id}")
        graph_view.scroll_to_widget(focused_graph_node)

    def action_write_graph(self):
        self.notify("write_graph Action (DUMMY)")

    def action_load_graph(self):
        self.notify("load_graph action (DUMMY)")

    def action_undo(self):
        self.notify("undo action (DUMMY)")

    def action_redo(self):
        self.notify("redo action (DUMMY)")
