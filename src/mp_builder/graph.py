from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, VerticalScroll, ScrollableContainer, HorizontalScroll, Horizontal
from textual.widgets import Button, Static, Label, Placeholder, Input
from textual.widget import Widget
from textual.reactive import reactive
from textual import on

import networkx as nx
import os

from rich.console import RenderableType

from rich.text import Text
from rich.align import Align

from mp_builder.dialogs import PipelineSelectDialogButton


NODE_HEIGHT = 7
NODE_WIDTH = 50
DEBUG_SYMBOLS = False
DEBUG_OUTLINES = False

class GraphNodeSpacer(Static):
    """A placeholder to position GraphNodes"""
    DEFAULT_CSS = f"""
    GraphNodeSpacer {{
        height: {NODE_HEIGHT};
        width: {NODE_WIDTH};
    }}
    """

    def compose(self) -> ComposeResult:
        yield Static()


class GraphEdge(Widget):
    """Represents an edge between two nodes."""

    TREE_GUIDES = [
        '────→',
        '──┬─→',
        '  ├─→',
        '  └─→',
        '  │  ',
        '     '
    ]

    DEFAULT_CSS = """
    GraphEdge {
        width: 8
    }
    """
    def __init__(self, in_breadths: list[int], out_breadths: list[list[int]], *args, **kwargs):
        assert(len(out_breadths) == len(in_breadths))
        self.in_breadths = in_breadths
        self.out_breadths = out_breadths
        super().__init__(*args, **kwargs)

    def render(self) -> RenderableType:
        """Render the edge as an arrow pointing to the target node."""
    
        out = ("ST" if DEBUG_SYMBOLS else "" + os.linesep) * (NODE_HEIGHT // 2)

        for b in range(len(self.out_breadths)):
            out_brds = self.out_breadths[b]
            in_brd = self.in_breadths[b]

            prev_brd = 0
            if b > 0:
                if len(self.out_breadths[b - 1]) > 0:
                    prev_brd = self.out_breadths[b - 1][-1]
                else:
                    prev_brd = self.in_breadths[b - 1]

            for j in range(in_brd - prev_brd):
                mult = NODE_HEIGHT if j > 0 or b == 0 else (NODE_HEIGHT - 1)
                symbol = self.TREE_GUIDES[5] if not DEBUG_SYMBOLS else "SP"
                out += (symbol + os.linesep) * mult
            
            if len(out_brds) == 0:              # HAS NO CHILDREN
                symbol = self.TREE_GUIDES[5] if not DEBUG_SYMBOLS else "NO"
                out += symbol + os.linesep

            if len(out_brds) == 1:              # HAS EXACTLY ONE CHILD
                out += self.TREE_GUIDES[0] + os.linesep

            elif len(out_brds) > 1:             # HAS MANY CHILDREN
                for i, child_brd in enumerate(out_brds):
                    if i == 0:   # First Branch
                        out += self.TREE_GUIDES[1] + os.linesep

                    else:

                        # Extend edge down while there is downstream branching in child nodes
                        # for _ in range(brd - out_brds[i-1]):
                        for j in range(child_brd - out_brds[i-1]):
                            mult = NODE_HEIGHT if j > 0 else (NODE_HEIGHT - 1)
                            symbol = self.TREE_GUIDES[4] if not DEBUG_SYMBOLS else "EX"
                            out += (symbol + os.linesep) * mult
                        
                        if i == len(out_brds) - 1:   # Last branch
                            out += self.TREE_GUIDES[3] + os.linesep

                        else:                        # More branches below
                            out += self.TREE_GUIDES[2] + os.linesep

        #return Panel(out)
        return Text(out)


class AddNodeButton(Button):
    """Button to add a new node."""
    
    DEFAULT_CSS = """
    AddNodeButton {
        width: 50%;
        max-width: 3;
        height: 100%;
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
        height: 100%;
        dock: left;
    }
    
    ButtonContainer > RemoveNodeButton {
        height: 100%;
        dock: right;
    }
    """

    def __init__(self, node_id, *args, **kwargs):
        self.node_id = node_id
        super().__init__(*args, **kwargs)
        self.id = "btn_ctn_" + node_id

    def compose(self):
        yield AddNodeButton(">", id=f"add_btn_{self.node_id}")
        yield RemoveNodeButton("X", id=f"remove_btn_{self.node_id}")

class GraphNode(Container):
    """A node in the graph visualization."""
    DEFAULT_CSS = f"""
    GraphNode {{
        width: {NODE_WIDTH};
        border: solid green;
        height: {NODE_HEIGHT};
    }}

    GraphNode > Horizontal {{
        content-align: center middle;
        height: 100%;
        margin: 0 1 0 1;  /* top right bottom left */
    }}

    GraphNode > Horizontal > PipelineSelectDialogButton {{
        width: 10%;
        min-width: 10%;
    }}
    
    GraphNode > Horizontal > Input {{
        width: 90%;
        height: 3;
        margin: 0;
    }}

    GraphNode > Horizontal > Input.dirty {{
        border: dashed yellow; /* Indicate unsaved changes */
    }}
    
    GraphNode > Static {{
        margin: 0 0 0 1;
        width: 90%;
    }}
    
    GraphNode > ButtonContainer {{
        dock: right;
        width: 10%;
        min-width: 7;
        height: 100%;
        padding: 0 0;
    }}
    """
    def __init__(self, node_data: dict, *args, **kwargs):
        self.node_data = node_data
        self._is_dirty = False
        super().__init__(*args, **kwargs)
        # wait for superclass for id to be initialized
        self._input_id = f"input-{self.id}"

    @property
    def name(self):
        return self.node_data.get("name", self.id)
    
    @name.setter
    def name(self, value: str):
        self.node_data["name"] = value

    @property
    def pipeline_type(self):
        if self.node_data.get("is_local", False):
            return "local"
        if self.node_data.get("is_nfcore", False):
            return "nf-core"
        return "no_pipeline"
    
    @property
    def pipeline_status(self):
        return self.node_data.get("pipeline_status", "no_status")
        
    @property
    def node_description(self):
        return f"{self.id} (d: {self.node_data.get("depth", "-")} b: {self.node_data.get("breadth", "-")}) {self.pipeline_type}"

    def compose(self) -> ComposeResult:

        #    yield Static(self.id)
        yield Static(self.node_description)
        yield Horizontal(
            Input(value=self.name, id=self._input_id),
            PipelineSelectDialogButton(node_data=self.node_data)
        )
        yield ButtonContainer(node_id=self.id)

    def _update_dirty_state(self, new_value):
        is_now_dirty = new_value != self.name

        if is_now_dirty != self._is_dirty:
            input_widget = self.query_one(f"#{self._input_id}")
            self._is_dirty = is_now_dirty
            input_widget.set_class(is_now_dirty, "dirty")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle the Input submitted event (Enter pressed)."""
        # Prevent the event from bubbling further up the DOM
        # if you don't want parent widgets to react to it.
        #event.stop()

        self.name = event.value.strip()
        self._is_dirty = False
        input_widget = self.query_one(f"#{self._input_id}")
        input_widget.remove_class("dirty")

        # --- Perform your desired action here ---
        self.notify(f"Enter pressed on Input in Node '{self.id}'. New potential ID: '{self.name}'")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Called whenever the Input value changes."""

        # Only react to changes in our specific input
        if event.input.id == self._input_id:

            #TODO: Check if we can actually access the value
            self._update_dirty_state(event.input.value)
            event.stop() # Stop propagation if needed


class GraphView(Container):
    """Container for the graph visualization with horizontal scrolling."""
    
    DEFAULT_CSS = f"""
    GraphView {{
        height: auto;
        width: auto;
        {"border: thick $accent-darken-2; /* Debugging border */" if DEBUG_OUTLINES else ""}
    }}

    GraphView > Horizontal {{
        /* Let this container size itself based on its content */
        width: auto;
        height: auto;
        /* Add some visual space between columns if desired */
        /* grid-gutter-horizontal: 5; */ /* If using grid layout */
        /* Or use margin on Vertical below */
        {"border: thick $accent-darken-2; /* Debugging border */" if DEBUG_OUTLINES else ""}
        content-align: center middle;
    }}

    /* Each vertical column representing a layer */
    GraphView > Horizontal > Vertical {{
        width: auto; /* Let column width be determined by nodes inside */
        height: auto; /* Let column height grow with nodes/spacers */
        /* border: round $accent-lighten-2; */ /* Debugging border */
        /* Add space between columns */
        /* margin-right: 5; */ /* Example spacing */
        /* Align items top-center within the column */
        align: center top;
    }}

    GraphView > Horizontal > Vertical > GraphEdge {{
        max-width: 8;
        height: auto;
        content-align: center middle;
    }}

    Placeholder {{
        height: 5;
    }}
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

        with Horizontal(id="graph_container"):
            layers = list(nx.bfs_layers(self.graph, "node0"))

            for i, layer in enumerate(layers):
                # TODO: Can this be avoided by recycling next_layer from below?
                layer = sorted(layer, key=lambda n: self.graph.nodes[n].get("breadth", 0))
                
                # Draw Nodes
                with Vertical():
                    tot_breadth = 0
                    for j, node in enumerate(layer):

                        node_depth = self.graph.nodes[node].get("depth")
                        node_breadth = self.graph.nodes[node].get("breadth")

                        #yield Static("Depth: " + str(node_depth) + " Breadth: " + str(node_breadth))
                        
                        # push node back, if it is also a child of a downstream node
                        if node_depth > i and len(layers) > i+1:
                            layers[i+1].append(node)
                            continue
                        
                        # if a downstream node has many children, insert spacing according to breadth
                        while tot_breadth + j < node_breadth:
                            tot_breadth += 1
                            yield GraphNodeSpacer()

                        # Draw the node
                        yield GraphNode(id=f"{node}", node_data=self.graph.nodes[node])
                        
                        # TODO: Draw the edges

                # Draw edges
                with Vertical():

                    if i == len(layers) - 1:
                        # Leaves, don't draw edges
                        continue
                    
                    else:
                        # Construct next layer
                        next_layer = [
                            list(sorted(map(lambda e: e[1], self.graph.out_edges(n)),
                                   key=lambda n: self.graph.nodes[n].get("breadth", 0)))
                            for n in layer
                        ]
                        #layers[i+1] = next_layer  # keep the sorting

                        in_breadths = list(map(lambda n: self.graph.nodes[n].get("breadth"), layer))
                        out_breadths = [list(map(lambda n: self.graph.nodes[n].get("breadth"), descs)) for descs in next_layer]

                        yield GraphEdge(in_breadths=in_breadths, out_breadths=out_breadths)
