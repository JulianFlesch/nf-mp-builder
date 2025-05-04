from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Button, Header, Footer, TabbedContent, TabPane
from textual.css.query import NoMatches
import networkx as nx

from mp_builder.node_view import NodeView
from mp_builder.edge_view import EdgeView
from mp_builder.graph import GraphView
from mp_builder.utils import save_graph_to_file, load_gaph_from_file


DEBUG_OUTLINES = True


class MetaPipelinesApp(App):
    """Main application for graph visualization."""
    
    DEFAULT_CSS = f"""    
    MetaPipelinesApp {{
        background: #1f1f1f;
    }}

    TabbedContent {{
        { "border: thick $accent-darken-1;" if DEBUG_OUTLINES else "" }
    }}

    TabPane {{
        { "border: thick red;" if DEBUG_OUTLINES else "" }
    }}

    TabPane > ScrollableContainer {{
        { "border: thick dodgerblue;" if DEBUG_OUTLINES else "" }
    }}
    """
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit"),
        ("w", "write_graph", "Save"),
        ("o", "load_graph", "Open"),
        ("ctrl+z", "undo", "Undo"),
        ("ctrl+y", "redo", "Redo")
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
        with TabbedContent():
            with TabPane("Graph"):
                with ScrollableContainer(id="graph-scroll"):
                    yield GraphView(self.graph)  # pass reference
            with TabPane("Nodes"):
                with ScrollableContainer(id="node-scroll"):
                    yield NodeView()
            with TabPane("Edges"):
                with ScrollableContainer(id="edge-scroll"):
                    yield EdgeView()
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
            to_remove = nx.descendants(self.graph, node_id)
            self.graph.remove_node(node_id)
            for n in to_remove:
                self.graph.remove_node(n)

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
        file = "mp-builder-graph.json"
        save_graph_to_file(self.graph, file)

    def action_load_graph(self):
        self.notify("load_graph action (DUMMY)")
        file = "mp-builder-graph.json"
        self.graph = load_gaph_from_file(file).copy()
        
        # Redraw the graph
        graph_view = self.query_one(GraphView)
        graph_view.graph = self.graph
        graph_view.refresh(recompose=True)

    def action_undo(self):
        self.notify("undo action (DUMMY)")

    def action_redo(self):
        self.notify("redo action (DUMMY)")
