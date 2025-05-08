"""
Run complete transport network analysis and save results.
"""

import os
import pickle
import time
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv

# Import our project modules
from src.data_processing.gtfs_loader import GTFSLoader
from src.graph_analysis.graph_builder import TransportGraphBuilder
from src.graph_analysis.community_detection import CommunityDetector
from src.symbolic_ai.knowledge_base import TransportKnowledgeBase

def main():
    # Start timing
    start_time = time.time()
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment variables
    gtfs_url = os.getenv("GTFS_URL")
    data_dir = os.getenv("DATA_DIR")
    
    # Create results directory if it doesn't exist
    if not os.path.exists("results"):
        os.makedirs("results")
    
    # Step 1: Load GTFS data
    print("\n1. Loading GTFS data...")
    loader = GTFSLoader(gtfs_url, data_dir)
    
    if not os.path.exists(os.path.join(data_dir, "stops.txt")):
        gtfs_data = loader.process()
    else:
        gtfs_data = loader.load_data()
    
    # Step 2: Build graph
    print("\n2. Building transport network graph...")
    builder = TransportGraphBuilder(gtfs_data)
    G = builder.build_graph(sample_size=1000)  # Adjust sample size as needed
    
    # Save graph
    print("Saving graph...")
    with open("results/transport_graph.pkl", "wb") as f:
        pickle.dump(G, f)
    
    # Print graph statistics
    stats = builder.get_graph_stats()
    print("\nGraph Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Save graph statistics
    with open("results/graph_stats.pkl", "wb") as f:
        pickle.dump(stats, f)
    
    # Step 3: Detect communities
    print("\n3. Detecting communities...")
    detector = CommunityDetector(G)
    partition = detector.detect_communities_louvain()
    
    # Save partition
    with open("results/communities_partition.pkl", "wb") as f:
        pickle.dump(partition, f)
    
    # Analyze communities
    print("\nAnalyzing communities...")
    community_analysis = detector.analyze_communities()
    
    # Save community analysis
    with open("results/community_analysis.pkl", "wb") as f:
        pickle.dump(community_analysis, f)
    
    # Visualize communities
    print("\nVisualizing communities...")
    detector.visualize_communities(output_file="results/communities_visualization.png")
    
    # Step 4: Identify critical nodes
    print("\n4. Identifying critical nodes...")
    critical_nodes = detector.identify_critical_nodes(top_n=30)
    
    # Save critical nodes
    with open("results/critical_nodes.pkl", "wb") as f:
        pickle.dump(critical_nodes, f)
    
    # Create critical nodes DataFrame for easier analysis
    critical_df = pd.DataFrame([
        {
            'node_id': node_id,
            'name': G.nodes[node_id].get('name', 'Unknown'),
            'community': partition[node_id],
            'centrality': score,
            'degree': G.degree[node_id],
            'lat': G.nodes[node_id].get('lat', 0),
            'lon': G.nodes[node_id].get('lon', 0)
        }
        for node_id, score in critical_nodes
    ])
    
    # Save critical nodes DataFrame
    critical_df.to_csv("results/critical_nodes.csv", index=False)
    
    # Step 5: Perform symbolic AI analysis
    print("\n5. Creating symbolic knowledge base and performing reasoning...")
    kb_creator = TransportKnowledgeBase(G, partition)
    kb = kb_creator.create_knowledge_base()
    
    # Save knowledge base
    with open("results/knowledge_base.pkl", "wb") as f:
        pickle.dump(kb, f)
    
    # Perform symbolic reasoning
    symbolic_results = kb_creator.perform_symbolic_reasoning(critical_nodes)
    
    # Save symbolic results
    with open("results/symbolic_results.pkl", "wb") as f:
        pickle.dump(symbolic_results, f)
    
    # Print gateway nodes information
    print("\nTop Gateway Nodes (connecting multiple communities):")
    for i, (node_id, data) in enumerate(symbolic_results['gateway_nodes'][:10], 1):
        print(f"{i}. {data['name']} (Community {data['community']}):")
        print(f"   Connects to {data['num_communities']} communities: {data['connected_communities']}")
    
    # Print community dependencies
    print("\nCommunity Dependencies:")
    for i, (comm_id, data) in enumerate(symbolic_results['community_dependencies'][:5], 1):
        print(f"{i}. Community {comm_id}:")
        print(f"   Connected to {data['num_connections']} communities: {data['connected_to']}")
    
    # Calculate total processing time
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\nComplete analysis finished in {total_time:.2f} seconds.")
    print("All results saved to the 'results' directory.")
    print("\nTo view the interactive dashboard, run:")
    print("python dashboard.py")

if __name__ == "__main__":
    main()