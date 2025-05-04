import os
import json

import networkx as nx
from networkx.readwrite import json_graph


def save_graph_to_file(graph: nx.DiGraph, file: str):
    data = json_graph.adjacency_data(graph)
    s = json.dumps(data, indent=2)

    with open(file, "w") as f:
        f.write(s)


def load_gaph_from_file(file: str):
    
    with open(file, "r") as f:
        data = json.loads(f.read())
    
    g = json_graph.adjacency_graph(data)

    return g
