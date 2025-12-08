from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer, Grid
from textual.screen import Screen
from textual.widgets import Button, Header, Footer, TabbedContent, TabPane, Input, Label
from textual.css.query import NoMatches
import networkx as nx

from mp_builder.gui.dialogs import QuitScreen
from mp_builder.gui.node_view import NodeView
from mp_builder.gui.edge_view import EdgeView
from mp_builder.gui.graph import GraphView
from mp_builder.utils import load_graph_from_file
from mp_builder.config import MetaworkflowGraph


DEBUG_OUTLINES = True
NODE_HEIGHT = 5
NODE_WIDTH = 10

class MetaPipelinesApp(App):
    """Main application for graph visualization."""
    debug_outlines = False
    node_height: int = None
    node_width: int = None

    CSS_PATH = [
        "styles/styles.tcss",
        "styles/dialogs.tcss",
    ]

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "request_quit", "Quit"),
        ("w", "write_graph", "Save"),
        ("o", "load_graph", "Open"),
        ("ctrl+z", "undo", "Undo"),
        ("ctrl+y", "redo", "Redo"),
        ("l", "lock", "Lock")
    ]
    
    def __init__(self, metaworkflow_graph: MetaworkflowGraph):
        self._next_node_number = 1
        self.mg = metaworkflow_graph
        super().__init__()

        css_variables = self.app.get_css_variables()

        css_variables["node_height"] = 10
        css_variables["node_width"] = 20

        self.refresh_css()
        try:
            print (self.get_css_variables())
            self.node_height = self.get_css_variables()["node_height"]
            self.node_width = self.get_css_variables()["node_width"]
        except KeyError:
            #raise RuntimeError("Required $node_height or $node_width not set in the .tcss stylesheet!")
            pass

    @property
    def next_node_id(self):
        self._next_node_number += 1
        nid = f"node{self._next_node_number}"
        existing_node_ids = self.mg.G.nodes()

        while nid in existing_node_ids:
            self._next_node_number += 1
            nid = f"node{self._next_node_number}"

        return nid

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane("Graph"):
                with ScrollableContainer(id="graph-scroll"):
                    yield GraphView(self.mg)  # pass reference
            with TabPane("Nodes"):
                with ScrollableContainer(id="node-scroll"):
                    yield NodeView(self.mg)
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

        # Handle redraw on pipeline dialog confirm 
        elif button_id == "confirm-dialog-button":

            # TODO: This does not scroll to the selected node
            graph_view = self.query_one(GraphView)
            graph_view.refresh(recompose=True)
            
            # Redraw the node view
            node_view = self.query_one(NodeView)
            node_view.refresh(recompose=True)

            # Redraw the edge view
            node_view = self.query_one(EdgeView)
            node_view.refresh(recompose=True)

    
    def on_input_submitted(self, event: Input.Submitted):
        # TODO: This catches input update events from graph view etc. Can this be more specific?

        event.stop()

        # TODO: Need to redraw graph_view for events in other views?

        # Redraw the node view
        node_view = self.query_one(NodeView)
        node_view.refresh(recompose=True)

        # Redraw the edge view
        node_view = self.query_one(EdgeView)
        node_view.refresh(recompose=True)

    
    def _add_node(self, parent_id: str) -> None:
            """Add a new node after the parent node."""
        #try:
            graph_view = self.query_one(GraphView)
            
            # Create a new node
            new_node_id = self.next_node_id

            # only update the original graph
            self.mg.G.add_edge(parent_id, new_node_id)

            # Redraw the node view
            #node_view = self.query_one(NodeView)
            #node_view.refresh(recompose=True)

            # Redraw the edge view
            #node_view = self.query_one(EdgeView)
            #node_view.refresh(recompose=True)

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
            to_remove = nx.descendants(self.mg.G, node_id)
            self.mg.G.remove_node(node_id)
            for n in to_remove:
                self.mg.G.remove_node(n)

            # Redraw the graph
            graph_view = self.query_one(GraphView)
            graph_view.refresh(recompose=True)

            # Redraw the node view
            node_view = self.query_one(NodeView)
            node_view.refresh(recompose=True)

            # Redraw the edge view
            node_view = self.query_one(EdgeView)
            node_view.refresh(recompose=True)

            self.notify(f"Node removed")
        except NoMatches:
            self.notify("Could not find node to remove")
    
    def scroll_to_node(self, graph_view: GraphView, node_id: str) -> None:
        """Scroll the view to show a specific node."""
        focused_graph_node = self.query_one(f"GraphNode#{node_id}")
        graph_view.scroll_to_widget(focused_graph_node)

    def action_request_quit(self):
        self.push_screen(QuitScreen())

    def action_write_graph(self):
        file = "metapipeline.yaml"
        self.notify(f"Writing graph to {file}")
        self.mg.to_file(file)

    def action_load_graph(self):
        self.notify("load_graph action (DUMMY)")
        file = "metapipeline.yaml"
        self.mg = MetaworkflowGraph.from_file(file)
        
        # Redraw the graph
        graph_view = self.query_one(GraphView)
        graph_view.mg = self.mg
        graph_view.refresh(recompose=True)

        # Redraw the node view
        node_view = self.query_one(NodeView)
        node_view.mg = self.mg
        node_view.refresh(recompose=True)

        #TODO: Redraw Edge View ?

    def action_undo(self):
        self.notify("undo action (DUMMY)")

    def action_redo(self):
        self.notify("redo action (DUMMY)")

    def action_lock(self):
        self.notify("lock the graph action (DUMMY)")
