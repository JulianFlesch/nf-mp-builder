from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, ScrollableContainer, HorizontalScroll
from textual.widgets import Button, Static
from textual.widget import Widget
from textual.reactive import reactive

import networkx as nx
import os

from rich.console import RenderableType

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


class GraphNodeSpacer(Container):
    """A placeholder to position GraphNodes"""
    DEFAULT_CSS = """
    GraphNodeSpacer {
        height: 5;
        width: 20;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static()

class GraphView(Container):
    """Container for the graph visualization with horizontal scrolling."""
    
    DEFAULT_CSS = """
    GraphView {
        width: 100%;
    }

    GraphView > HorizontalScroll > Vertical {
        width: auto; 
        content-align: center middle;
    }

    GraphView > HorizontalView > Vertical > GraphEdge {
        max-width: 8;
        height: 100%;
        content-align: center middle;
    }

    Placeholder {
        height: 5;
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

        # node breadth is tracked globally
        breadth = 0

        while len(stack) > 0:

            # get top of stack
            current_node = stack.pop(0)

            if not self.graph.nodes[current_node].get("visited", False):
                # position the node relative to ancestors
                depth = 0
                for ancestor in nx.ancestors(self.graph, current_node):
                    depth = max(self.graph.nodes[ancestor].get("depth", 0) + 1, depth)
                    #breadth = min(self.graph.nodes[ancestor].get("breadth", 0), breadth + 1)

                self.graph.nodes[current_node]["depth"] = depth
                self.graph.nodes[current_node]["breadth"] = breadth
                self.graph.nodes[current_node]["visited"] = True

                # We have to infer direct descendants from edge data
                node_descendants = list(map(lambda edge: edge[1], nx.edges(self.graph, current_node)))
                stack = node_descendants + stack

                if len(node_descendants) == 0:
                    breadth += 1

    def compose(self) -> ComposeResult:

        self._unvisit_graph()
        self._layout_graph()

        import json
        yield Static("GraphView. Size: " + str(len(self.graph)) + "Node Data: " + json.dumps(nx.get_node_attributes(self.graph, "depth")))
        with HorizontalScroll(id="graph_container"):
            layers = nx.bfs_layers(self.graph, "node0")
            for i, layer in enumerate(layers):
                with Vertical(id=f"vrt_nds_{i}"):
                    layer = sorted(layer, key=lambda n: self.graph.nodes[n].get("breadth", 0))
                    for j, node in enumerate(layer):

                        node_depth = self.graph.nodes[node].get("depth")
                        node_breadth = self.graph.nodes[node].get("breadth")

                        #yield Static("Depth: " + str(node_depth) + " Breadth: " + str(node_breadth))
                        
                        # push node back, if it is also a child of a downstream node
                        if node_depth > i and len(layers) > i+1:
                            layers[i+1].append(node)
                            continue
                        
                        # if a downstream node has many children, insert spacing according to breadth
                        for k in range(j, node_breadth):
                            #yield Placeholder(id=f"pchld-{i}-{j}-{k}")
                            yield GraphNodeSpacer()
                        
                        # Draw the node
                        yield GraphNode(id=f"{node}")
                        
                        # TODO: Draw the edges

                #if i < len(self.graph) - 1:
                #    with Vertical(id=f"vrt_egs_{node}"):
                #        yield GraphEdge(out_degree=1, node_height=5)
