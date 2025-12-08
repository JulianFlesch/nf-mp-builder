from mp_builder.gui.ui import MetaPipelinesApp
from mp_builder.config import MetaworkflowGraph

def main():
    
    mg = MetaworkflowGraph()
    mg.G.add_node(MetaworkflowGraph.ROOT_NODE)
    app = MetaPipelinesApp(mg)
    app.run()
