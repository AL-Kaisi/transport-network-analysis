"""
Test script for the community detection module.
"""

import os
import time
from dotenv import load_dotenv
from src.data_processing.gtfs_loader import GTFSLoader
from src.graph_analysis.graph_builder import TransportGraphBuilder
from src.graph_analysis.community_detection import CommunityDetector
import matplotlib.pyplot as plt
import networkx as nx

# Load environment variables
load_dotenv()

def main():
    # Get configuration from environment variables
    gtfs_url = os.getenv("GTFS_URL")
    data_dir = os.getenv("DATA_DIR")
    
    # Load GTFS data
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
    G = builder.build_graph(sample_size=1000)  # Sample for faster testing
    
    # Detect communities
    print("\nDetecting communities...")
    detector = CommunityDetector(G)
    
    # Time the community detection process
    start_time = time.time()
    partition = detector.detect_communities_louvain()
    detection_time = time.time() - start_time
    
    print(f"\nCommunities detected in {detection_time:.2f} seconds")
    
    # Analyze communities
    analysis = detector.analyze_communities()
    print(f"\nNetwork modularity: {analysis['modularity']:.4f}")
    print(f"Number of communities: {analysis['num_communities']}")
    
    # Print information about the largest communities
    print("\nLargest communities:")
    communities_by_size = sorted(
        analysis['communities'].items(), 
        key=lambda x: x[1]['size'], 
        reverse=True
    )
    
    for i, (comm_id, comm_data) in enumerate(communities_by_size[:5], 1):
        print(f"{i}. Community {comm_id}:")
        print(f"   Size: {comm_data['size']} nodes")
        print(f"   Density: {comm_data['density']:.4f}")
        print(f"   Avg. Degree: {comm_data['avg_degree']:.2f}")
        if comm_data['center_lat'] and comm_data['center_lon']:
            print(f"   Center: ({comm_data['center_lat']:.6f}, {comm_data['center_lon']:.6f})")
            print(f"   Radius: {comm_data['radius']:.6f}")
    
    # Visualize communities
    print("\nVisualizing communities...")
    detector.visualize_communities()
    
    # Identify critical nodes
    print("\nIdentifying critical nodes...")
    critical_nodes = detector.identify_critical_nodes(top_n=10)
    
if __name__ == "__main__":
    main()