from rich.tree import Tree
from rich.console import Console
import random
import string

def generate_random_string(length=6):
    """Generate a random string of letters and digits."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def create_random_tree(depth=3, max_children=4):
    """
    Create a random tree with specified maximum depth.
    
    Args:
        depth: Maximum depth of the tree
        max_children: Maximum number of children per node
    
    Returns:
        A rich.tree.Tree object
    """
    # Create the root node with a random label
    root_label = f"Root-{generate_random_string()}"
    tree = Tree(root_label, guide_style="bold bright_blue")
    
    # Function to recursively add nodes
    def add_nodes(parent_node, current_depth, max_depth):
        if current_depth >= max_depth:
            return
            
        # Random number of children for this node
        num_children = random.randint(1, max_children)
        
        for i in range(num_children):
            child_label = f"Node-{generate_random_string()}"
            child = parent_node.add(child_label, guide_style="bright_green")
            
            # Recursively add children to this node
            add_nodes(child, current_depth + 1, max_depth)
    
    # Start adding nodes from the root
    add_nodes(tree, 1, depth)
    
    return tree

if __name__ == "__main__":
    # Set a random seed for reproducibility (optional)
    random.seed(42)
    
    # Create a random tree with depth 3
    random_tree = create_random_tree(depth=3)
    
    # Create a console and print the tree sideways
    console = Console()
    console.print(random_tree, width=100, overflow="fold")
    