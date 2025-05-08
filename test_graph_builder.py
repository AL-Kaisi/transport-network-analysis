"""
Test script for the graph builder module.
"""

import os
import time
from dotenv import load_dotenv
from src.data_processing.gtfs_loader import GTFSLoader
from src.graph_analysis.graph_builder import TransportGraphBuilder
import matplotlib.pyplot as plt
import networkx as nx

# Load environment variables
load_dotenv()

def main():
    # Get configuration from environment variables
    gtfs_url = os.getenv("GTFS_URL")
    data_dir = os.getenv("DATA_DIR")
    
    # Create GTFS loader
    loader = GTFSLoader(gtfs_url, data_dir)
    
    # Check if data already exists, otherwise download it
    if not os.path.exists(os.path.join(data_dir, "stops.txt")):
        print("Downloading GTFS data...")
        gtfs_data = loader.process()
    else:
        print("Loading existing GTFS data...")
        gtfs_data = loader.load_data()
    
    # Build graph from a sample of trips
    print("\nBuilding transport network graph...")
    builder = TransportGraphBuilder(gtfs_data)
    
    # Time the graph building process
    start_time = time.time()
    G = builder.build_graph(sample_size=1000)  # Sample for faster testing
    build_time = time.time() - start_time
    
    print(f"\nGraph built in {build_time:.2f} seconds")
    
    # Get graph statistics
    stats = builder.get_graph_stats()
    print("\nGraph Statistics:")
    for key, value in stats.items():
        print(f"- {key}: {value}")
    
    # Visualize a small portion of the graph
    print("\nVisualizing a subset of the graph (this might take a moment)...")
    
    # Take a subgraph of the 100 highest degree nodes for visualization
    degrees = dict(G.degree())
    top_nodes = sorted(degrees, key=degrees.get, reverse=True)[:100]
    subgraph = G.subgraph(top_nodes)
    
    plt.figure(figsize=(12, 10))
    
    # Use geographical coordinates for node positions
    pos = {}
    for node in subgraph.nodes():
        node_data = G.nodes[node]
        pos[node] = (node_data['lon'], node_data['lat'])
    
    # Draw the subgraph
    nx.draw_networkx(
        subgraph, 
        pos=pos,
        with_labels=False,
        node_size=50,
        node_color='lightblue',
        edge_color='gray',
        alpha=0.7
    )
    
    plt.title(f"Greater Manchester Transport Network\n(Subset of {len(subgraph)} nodes)")
    plt.axis('off')
    plt.tight_layout()
    
    # Save the visualization
    plt.savefig("transport_network_subset.png", dpi=300)
    print("Visualization saved to transport_network_subset.png")
    
if __name__ == "__main__":
    main()