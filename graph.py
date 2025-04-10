from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer, HorizontalScroll
from textual.widgets import Button, Static, Header, Footer, Label
from textual.widget import Widget
from textual.reactive import reactive
from textual.css.query import NoMatches
import uuid
import networkx as nx
import os

from rich.console import RenderableType
from rich.panel import Panel
from rich.segment import Segment
from rich.style import Style
import rich.console
from rich.tree import Tree
from rich.text import Text


class GraphEdge(Widget):
    """Represents an edge between two nodes."""
    
    #ASCII_GUIDES = ("    ", "|   ", "+-- ", "`-- ")

    DEFAULT_CSS = """
    GraphEdge {
        width: 8
    }
    """
    def __init__(self, out_degree: int, node_height: int=5):
        self.out_degree = out_degree
        self.node_height = node_height
        super().__init__()

    def render(self) -> RenderableType:
        """Render the edge as an arrow pointing to the target node."""

        out = os.linesep * (self.node_height // 2)

        if self.out_degree == 1:
            out += "----->"
        else:
            out += "--+-->" + os.linesep
        
            for i in range(self.out_degree - 1):
                out += ("  |   " + os.linesep)  * (self.node_height)
                out += "  +-->" + os.linesep

        #return Panel(out)
        return Text(out)


class AddNodeButton(Button):
    """Button to add a new node."""
    
    DEFAULT_CSS = """
    AddNodeButton {
        width: 50%;
        max-width: 3;
        height: 100%;
        max-height: 3;
        content-align: center middle;
        background: green;
        color: white;
        padding: 0 0;
    }
    """

class RemoveNodeButton(Button):
    """Button to remove a node."""
    
    DEFAULT_CSS = """
    RemoveNodeButton {
        width: 50%;
        max-width: 3;
        height: 100%;
        max-height: 3;
        content-align: center middle;
        background: red;
        color: white;
        padding: 0 0;
    }
    """

class ButtonContainer(Container):
    """
    Contains Add/Remove Buttons
    """

    DEFAULT_CSS = """
    ButtonContainer > AddNodeButton {
        dock: left;
    }
    
    ButtonContainer > RemoveNodeButton {
        dock: right;
    }
    """

    def __init__(self, node_id, *args, **kwargs):
        self.node_id = node_id
        super().__init__(*args, **kwargs)
        self.id = "btn_ctn_" + node_id

    def compose(self):
        yield AddNodeButton("+", id=f"add_btn_{self.node_id}")
        yield RemoveNodeButton("-", id=f"remove_btn_{self.node_id}")

class GraphNode(Container):
    """A node in the graph visualization."""
    DEFAULT_CSS = """
    GraphNode {
        width: 20;
        border: solid green;
        height: 5;
        padding: 0 0;
    }
    
    GraphNode > Static {
        width: 60%;
        height: 100%;
        text-align: center;
        content-align: center middle;
    }
    
    GraphNode > ButtonContainer {
        dock: right;
        width: 40%;
        height: 100%;
        padding: 0 0;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(self.id)
        yield ButtonContainer(node_id=self.id)


class GraphView(ScrollableContainer):
    """Container for the graph visualization with horizontal scrolling."""
    
    DEFAULT_CSS = """
    GraphView {
        width: 100%;
        height: 100%;
    }

    GraphView > HorizontalScroll > Vertical {
        height: 100%;
        width: auto;
        content-align: center middle;
    }

    GraphView > HorizontalView > Vertical > GraphEdge {
        max-width: 8;
        height: 100%;
        content-align: center middle;
    }
    """
    graph: nx.DiGraph

    def __init__(self, graph: nx.DiGraph):
        self.graph = graph
        super().__init__()

    def _unvisit_graph(self):
        for n in self.graph.nodes():
            self.graph.nodes[n]["visited"] = False
            self.graph.nodes[n]["depth"] = 0
            self.graph.nodes[n]["breadth"] = 0

    def _layout_graph(self):
        """
        DFS to assign node coordinates that aid drawing
        """
        # TODO: How to find root?
        # first node is currently always set as root:
        current_node = list(self.graph.nodes())[0]
        stack = [current_node]

        while len(stack) > 0:

            # get top of stack
            current_node = stack.pop(0)

            # position the node relative to ancestors
            depth, breadth = 1, 1
            for ancestor in nx.ancestors(self.graph, current_node):
                depth = max(self.graph.nodes[ancestor].get("depth", 0), depth)
                breadth = max(self.graph.nodes[ancestor].get("breadth", 0), breadth)
            
            #attr = nx.get_node_attributes(self.graph, current_node)
            self.graph.nodes[current_node]["depth"] = depth
            self.graph.nodes[current_node]["breadth"] = breadth

            if not self.graph.nodes[current_node].get("visited", False):
                self.graph.nodes[current_node]["visited"] = True
                stack += list(nx.descendants(self.graph, current_node))

    def compose(self) -> ComposeResult:

        self._unvisit_graph()
        self._layout_graph()

        yield Static("GraphView. Size: " + str(len(self.graph)))
        with Scroll(id="graph_container"):
            for i, layer in enumerate(nx.bfs_layers(self.graph, "node0")):
                with Vertical(id=f"vrt_nds_{i}"):
                    for node in layer: 
                        yield GraphNode(id=f"{node}")

                #if i < len(self.graph) - 1:
                #    with Vertical(id=f"vrt_egs_{node}"):
                #        yield GraphEdge(out_degree=1, node_height=5)

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
        ("q", "quit", "Quit"),
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
            #scroll_to_node(graph_view, new_node_id)
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


if __name__ == "__main__":

    g = nx.DiGraph()
    g.add_node("node0")
    app = MetaPipelinesApp(graph=g)
    app.run()
