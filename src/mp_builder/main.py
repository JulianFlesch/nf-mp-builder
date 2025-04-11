from mp_builder.ui import MetaPipelinesApp
import networkx as nx

def main():
    
    g = nx.DiGraph()
    g.add_node("node0")
    app = MetaPipelinesApp(graph=g)
    app.run()
